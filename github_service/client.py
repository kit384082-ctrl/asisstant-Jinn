"""Safe, small wrapper around the GitHub API used by Genie."""

from __future__ import annotations

import logging
import posixpath
from typing import Any

logger = logging.getLogger(__name__)

try:
    from github import Auth, Github
    from github.GithubException import GithubException
except ImportError:  # Lets the setup GUI start before requirements are installed.
    Auth = None  # type: ignore[assignment]
    Github = None  # type: ignore[assignment]

    class GithubException(Exception):  # type: ignore[no-redef]
        status = 0


class GitHubClient:
    def __init__(
        self,
        token: str,
        default_repo: str,
        *,
        branch: str = "main",
        github: Any | None = None,
    ):
        if branch != "main":
            raise ValueError("Genie разрешено работать только с веткой main.")
        if not token:
            raise ValueError("GitHub token is empty")
        if not default_repo or default_repo.count("/") != 1:
            raise ValueError("Repository must have the owner/repository format")
        if Github is None and github is None:
            raise RuntimeError(
                "Библиотека PyGithub не установлена. Выполните: "
                "pip install -r requirements.txt"
            )

        self.branch = branch
        self.repo_name = default_repo
        self.g = github
        if self.g is None:
            if Auth is None or Github is None:
                raise RuntimeError("PyGithub is unavailable")
            self.g = Github(auth=Auth.Token(token), timeout=20)

        try:
            self.repo = self.g.get_repo(self.repo_name)
            logger.info("Connected to repository: %s", self.repo_name)
        except GithubException:
            logger.exception("Failed to connect to repository %s", self.repo_name)
            self.close()
            raise

    def get_notifications(self) -> list[dict[str, Any]]:
        """Fetch up to five unread notifications from all repositories."""

        notifications: list[dict[str, Any]] = []
        if self.g is None:
            return notifications

        items = self.g.get_user().get_notifications(all=False, participating=False)
        for notification in items:
            notifications.append(
                {
                    "title": notification.subject.title,
                    "type": notification.subject.type,
                    "repo": notification.repository.full_name,
                    "url": getattr(notification.subject, "latest_comment_url", None),
                }
            )
            if len(notifications) >= 5:
                break
        return notifications

    def get_active_issues(self) -> list[dict[str, Any]]:
        """Fetch the three newest issues, excluding pull requests."""

        issues: list[dict[str, Any]] = []
        candidates = self.repo.get_issues(
            state="open", sort="created", direction="desc"
        )
        for issue in candidates:
            # GitHub's issues endpoint also returns pull requests.
            if getattr(issue, "pull_request", None) is not None:
                continue
            issues.append(
                {
                    "number": issue.number,
                    "title": issue.title,
                    "url": getattr(issue, "html_url", ""),
                }
            )
            if len(issues) >= 3:
                break
        return issues

    def get_active_prs(self) -> list[dict[str, Any]]:
        """Fetch the three newest open pull requests."""

        pull_requests: list[dict[str, Any]] = []
        for pull_request in self.repo.get_pulls(
            state="open", sort="created", direction="desc"
        )[:3]:
            pull_requests.append(
                {
                    "number": pull_request.number,
                    "title": pull_request.title,
                    "url": getattr(pull_request, "html_url", ""),
                }
            )
        return pull_requests

    def get_latest_action_status(self) -> str:
        """Return the latest workflow status on main."""

        runs = self.repo.get_workflow_runs(branch=self.branch)
        if runs.totalCount == 0:
            return "Запуски GitHub Actions в ветке main не найдены."
        run = runs[0]
        state = run.conclusion or run.status or "unknown"
        return f"Последний workflow «{run.name}»: {state}."

    def get_recent_commits_summary(self) -> str:
        """Return a concise summary of the latest three commits on main."""

        commits = self.repo.get_commits(sha=self.branch)[:3]
        messages = [commit.commit.message.splitlines()[0].strip() for commit in commits]
        messages = [message for message in messages if message]
        if not messages:
            return "В ветке main пока нет коммитов."
        formatted = "; ".join(f"«{message}»" for message in messages)
        return f"Последние коммиты: {formatted}."

    @staticmethod
    def normalize_file_path(file_path: str) -> str:
        """Validate a repository-relative POSIX path."""

        if not isinstance(file_path, str):
            raise TypeError("Путь к файлу должен быть строкой.")
        candidate = file_path.strip().replace("\\", "/")
        if not candidate or candidate.startswith("/") or "\x00" in candidate:
            raise ValueError("Укажите относительный путь к файлу.")
        parts = candidate.split("/")
        if any(part in {"", ".", ".."} for part in parts):
            raise ValueError("Путь не должен содержать пустые сегменты, «.» или «..».")
        normalized = posixpath.normpath(candidate)
        if normalized != candidate or normalized.startswith("../"):
            raise ValueError("Некорректный путь к файлу.")
        return normalized

    @staticmethod
    def append_text(existing: str, content: str) -> str:
        """Append text without introducing a blank first line or joining lines."""

        if not existing:
            return content
        separator = "" if existing.endswith("\n") else "\n"
        return existing + separator + content

    def append_to_file(self, file_path: str, content: str, commit_message: str) -> str:
        """Append UTF-8 text to a file strictly on ``main``; create if absent."""

        path = self.normalize_file_path(file_path)
        text = content.strip()
        if not text:
            raise ValueError("Нельзя добавить пустой текст.")
        message = commit_message.strip() or f"Update {path} via Genie"

        try:
            try:
                file_contents = self.repo.get_contents(path, ref=self.branch)
            except GithubException as exc:
                if exc.status != 404:
                    raise
                self.repo.create_file(
                    path=path,
                    message=message,
                    content=text,
                    branch=self.branch,
                )
                return f"Файл {path} создан в ветке main."

            if isinstance(file_contents, list):
                raise ValueError(f"{path} — каталог, а не файл.")  # noqa: TRY004
            try:
                existing = file_contents.decoded_content.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise ValueError(
                    "Можно изменять только текстовые UTF-8 файлы."
                ) from exc
            new_content = self.append_text(existing, text)
            self.repo.update_file(
                path=file_contents.path,
                message=message,
                content=new_content,
                sha=file_contents.sha,
                branch=self.branch,
            )
            return f"Текст добавлен в {path} в ветке main."
        except (GithubException, ValueError):
            logger.exception("Failed to modify %s", path)
            raise

    def verify_main_branch(self) -> bool:
        """Check that the only write target, ``main``, exists."""

        try:
            self.repo.get_branch(self.branch)
            return True
        except GithubException:
            logger.error("Repository %s has no main branch", self.repo_name)
            return False

    def close(self) -> None:
        close = getattr(getattr(self, "g", None), "close", None)
        if callable(close):
            close()

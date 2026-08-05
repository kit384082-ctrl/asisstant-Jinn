from github import Github, Auth
from github.GithubException import GithubException
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class GitHubClient:
    def __init__(self, token: str, default_repo: str):
        auth = Auth.Token(token)
        self.g = Github(auth=auth)
        self.repo_name = default_repo
        try:
            self.repo = self.g.get_repo(self.repo_name)
            logger.info(f"Successfully connected to repository: {self.repo_name}")
        except GithubException as e:
            logger.error(f"Failed to connect to repository {self.repo_name}: {e}")
            raise

    def get_notifications(self) -> List[Dict]:
        """Fetches unread notifications."""
        notifications = []
        for notif in self.g.get_user().get_notifications(participating=True):
            notifications.append({
                "title": notif.subject.title,
                "type": notif.subject.type,
                "repo": notif.repository.full_name
            })
            if len(notifications) >= 5: # Limit to 5 for speech
                break
        return notifications

    def get_active_issues(self) -> List[Dict]:
        """Fetches recent open issues."""
        issues = []
        for issue in self.repo.get_issues(state="open")[:3]:
            issues.append({
                "number": issue.number,
                "title": issue.title
            })
        return issues

    def get_active_prs(self) -> List[Dict]:
        """Fetches recent open pull requests."""
        prs = []
        for pr in self.repo.get_pulls(state="open")[:3]:
            prs.append({
                "number": pr.number,
                "title": pr.title
            })
        return prs

    def get_latest_action_status(self) -> str:
        """Gets the status of the latest workflow run on main branch."""
        try:
            runs = self.repo.get_workflow_runs(branch="main")
            if runs.totalCount > 0:
                latest_run = runs[0]
                return f"Workflow '{latest_run.name}' finished with status: {latest_run.conclusion or latest_run.status}"
            return "No recent workflow runs found."
        except Exception as e:
            logger.error(f"Error fetching actions status: {e}")
            return "Error retrieving GitHub Actions status."

    def get_recent_commits_summary(self) -> str:
        """Gets a summary of the latest 3 commits on main."""
        commits = self.repo.get_commits(sha="main")[:3]
        summary = "Recent commits: "
        for commit in commits:
            # Take only the first line of the commit message
            msg = commit.commit.message.split('\n')[0]
            summary += f"'{msg}', "
        return summary.strip(', ')

    def append_to_file(self, file_path: str, content: str, commit_message: str) -> str:
        """
        Appends content to a file strictly on the main branch.
        Creates the file if it doesn't exist.
        """
        target_branch = "main"
        try:
            # Check if file exists
            try:
                file_contents = self.repo.get_contents(file_path, ref=target_branch)
                # File exists, append
                existing_content = file_contents.decoded_content.decode('utf-8')
                new_content = existing_content + "\n" + content
                self.repo.update_file(
                    path=file_contents.path,
                    message=commit_message,
                    content=new_content,
                    sha=file_contents.sha,
                    branch=target_branch
                )
                return f"Successfully appended to {file_path} on main branch."

            except GithubException as e:
                if e.status == 404:
                    # File doesn't exist, create it
                    self.repo.create_file(
                        path=file_path,
                        message=commit_message,
                        content=content,
                        branch=target_branch
                    )
                    return f"Successfully created {file_path} on main branch."
                else:
                    raise
        except Exception as e:
            logger.error(f"Error modifying file: {e}")
            return f"Failed to modify file. Error: {str(e)}"

    def verify_main_branch(self):
        """A simple safety check to ensure we are operating on main."""
        try:
            self.repo.get_branch("main")
            return True
        except GithubException:
            logger.error("The repository does not have a 'main' branch!")
            return False

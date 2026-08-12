"""Core orchestration shared by the web GUI and voice-only mode."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any, Protocol

from config import Config

logger = logging.getLogger(__name__)


class GitHubOperations(Protocol):
    def get_notifications(self) -> list[dict[str, Any]]: ...

    def get_active_issues(self) -> list[dict[str, Any]]: ...

    def get_active_prs(self) -> list[dict[str, Any]]: ...

    def get_latest_action_status(self) -> str: ...

    def get_recent_commits_summary(self) -> str: ...

    def append_to_file(
        self, file_path: str, content: str, commit_message: str
    ) -> str: ...


def _language(value: str) -> str:
    code = value.split("-", 1)[0].casefold()
    return code if code in Config.SUPPORTED_LANGUAGES else "ru"


def _plural_ru(number: int, forms: tuple[str, str, str]) -> str:
    number = abs(number) % 100
    last = number % 10
    if 11 <= number <= 19:
        return forms[2]
    if last == 1:
        return forms[0]
    if 2 <= last <= 4:
        return forms[1]
    return forms[2]


TEXT = {
    "en": {
        "no_notifications": "There are no unread notifications.",
        "notifications": "Found {count} notification(s). Latest: {title}.",
        "no_issues": "There are no open issues.",
        "issues": "Found {count} issue(s). Latest: #{number} — {title}.",
        "no_prs": "There are no open pull requests.",
        "prs": "Open pull requests: {count}. Latest: #{number} — {title}.",
        "invalid_file": "The file path and text must be strings.",
        "empty_file": "I could not determine the text to append to the file.",
        "unknown": "I could not recognize the command. Try “show issues” or “add buy milk to notes.md”.",
    },
    "de": {
        "no_notifications": "Es gibt keine ungelesenen Benachrichtigungen.",
        "notifications": "{count} Benachrichtigung(en) gefunden. Neueste: {title}.",
        "no_issues": "Es gibt keine offenen Issues.",
        "issues": "{count} Issue(s) gefunden. Neueste: #{number} — {title}.",
        "no_prs": "Es gibt keine offenen Pull Requests.",
        "prs": "Offene Pull Requests: {count}. Neuester: #{number} — {title}.",
        "invalid_file": "Dateipfad und Text müssen Zeichenketten sein.",
        "empty_file": "Der Text zum Anhängen an die Datei konnte nicht bestimmt werden.",
        "unknown": "Der Befehl wurde nicht erkannt. Versuche „Issues anzeigen“ oder „Milch kaufen zu notes.md hinzufügen“.",
    },
    "es": {
        "no_notifications": "No hay notificaciones sin leer.",
        "notifications": "Se encontraron {count} notificación(es). Última: {title}.",
        "no_issues": "No hay issues abiertos.",
        "issues": "Se encontraron {count} issue(s). Último: #{number} — {title}.",
        "no_prs": "No hay pull requests abiertos.",
        "prs": "Pull requests abiertos: {count}. Último: #{number} — {title}.",
        "invalid_file": "La ruta del archivo y el texto deben ser cadenas.",
        "empty_file": "No pude determinar el texto que se debe añadir al archivo.",
        "unknown": "No pude reconocer el comando. Prueba «mostrar issues» o «añadir comprar leche a notes.md».",
    },
    "fr": {
        "no_notifications": "Il n’y a aucune notification non lue.",
        "notifications": "{count} notification(s) trouvée(s). Dernière : {title}.",
        "no_issues": "Il n’y a aucune issue ouverte.",
        "issues": "{count} issue(s) trouvée(s). Dernière : #{number} — {title}.",
        "no_prs": "Il n’y a aucune pull request ouverte.",
        "prs": "Pull requests ouvertes : {count}. Dernière : #{number} — {title}.",
        "invalid_file": "Le chemin du fichier et le texte doivent être des chaînes.",
        "empty_file": "Je n’ai pas pu déterminer le texte à ajouter au fichier.",
        "unknown": "Commande non reconnue. Essayez « afficher les issues » ou « ajouter acheter du lait à notes.md ».",
    },
}

PREFIX_TRANSLATIONS = {
    "en": {
        "Запуски GitHub Actions в ветке main не найдены.": "No GitHub Actions runs were found on main.",
        "В ветке main пока нет коммитов.": "There are no commits on main yet.",
        "Последний workflow": "Latest workflow",
        "Последние коммиты:": "Latest commits:",
        "Файл ": "File ",
        " создан в ветке main.": " was created on main.",
        "Текст добавлен в ": "Text was appended to ",
        " в ветке main.": " on main.",
    },
    "de": {
        "Запуски GitHub Actions в ветке main не найдены.": "Keine GitHub-Actions-Läufe auf main gefunden.",
        "В ветке main пока нет коммитов.": "Auf main gibt es noch keine Commits.",
        "Последний workflow": "Neuester Workflow",
        "Последние коммиты:": "Neueste Commits:",
        "Файл ": "Datei ",
        " создан в ветке main.": " wurde auf main erstellt.",
        "Текст добавлен в ": "Text wurde angehängt an ",
        " в ветке main.": " auf main.",
    },
    "es": {
        "Запуски GitHub Actions в ветке main не найдены.": "No se encontraron ejecuciones de GitHub Actions en main.",
        "В ветке main пока нет коммитов.": "Todavía no hay commits en main.",
        "Последний workflow": "Último workflow",
        "Последние коммиты:": "Últimos commits:",
        "Файл ": "El archivo ",
        " создан в ветке main.": " se creó en main.",
        "Текст добавлен в ": "Se añadió texto a ",
        " в ветке main.": " en main.",
    },
    "fr": {
        "Запуски GitHub Actions в ветке main не найдены.": "Aucune exécution GitHub Actions trouvée sur main.",
        "В ветке main пока нет коммитов.": "Il n’y a pas encore de commits sur main.",
        "Последний workflow": "Dernier workflow",
        "Последние коммиты:": "Derniers commits :",
        "Файл ": "Le fichier ",
        " создан в ветке main.": " a été créé sur main.",
        "Текст добавлен в ": "Texte ajouté à ",
        " в ветке main.": " sur main.",
    },
}


def _translate_github_response(response: str, language: str) -> str:
    if language == "ru":
        return response
    translated = response
    for source, target in PREFIX_TRANSLATIONS[language].items():
        translated = translated.replace(source, target)
    return translated


def execute_intent(
    intent: Mapping[str, Any],
    github_client: GitHubOperations,
    language: str = "ru",
) -> str:
    """Execute a validated intent and localize the user-facing response."""

    locale = _language(language)
    action = intent.get("action", "unknown")
    localized = TEXT.get(locale)

    if action == "check_notifications":
        notifications = github_client.get_notifications()
        if not notifications:
            return (
                localized["no_notifications"]
                if localized
                else "Непрочитанных уведомлений нет."
            )
        count = len(notifications)
        if localized:
            return localized["notifications"].format(
                count=count, title=notifications[0]["title"]
            )
        noun = _plural_ru(count, ("уведомление", "уведомления", "уведомлений"))
        return f"Найдено {count} {noun}. Последнее: {notifications[0]['title']}."

    if action == "check_issues":
        issues = github_client.get_active_issues()
        if not issues:
            return localized["no_issues"] if localized else "Открытых задач нет."
        count = len(issues)
        if localized:
            return localized["issues"].format(
                count=count,
                number=issues[0]["number"],
                title=issues[0]["title"],
            )
        noun = _plural_ru(count, ("задача", "задачи", "задач"))
        return f"Найдено {count} {noun}. Последняя: #{issues[0]['number']} — {issues[0]['title']}."

    if action == "check_prs":
        pull_requests = github_client.get_active_prs()
        if not pull_requests:
            return localized["no_prs"] if localized else "Открытых pull request’ов нет."
        count = len(pull_requests)
        if localized:
            return localized["prs"].format(
                count=count,
                number=pull_requests[0]["number"],
                title=pull_requests[0]["title"],
            )
        return (
            f"Открытых pull request’ов: {count}. Последний: "
            f"#{pull_requests[0]['number']} — {pull_requests[0]['title']}."
        )

    if action == "check_actions":
        return _translate_github_response(
            github_client.get_latest_action_status(), locale
        )

    if action == "recent_commits":
        return _translate_github_response(
            github_client.get_recent_commits_summary(), locale
        )

    if action == "append_file":
        file_path = intent.get("file_path") or "notes.md"
        content = intent.get("content") or ""
        commit_message = intent.get("commit_message") or "Update notes via Genie"
        if not isinstance(file_path, str) or not isinstance(content, str):
            return (
                localized["invalid_file"]
                if localized
                else "Путь к файлу и текст должны быть строками."
            )
        if not content.strip():
            return (
                localized["empty_file"]
                if localized
                else "Не удалось определить текст, который нужно добавить в файл."
            )
        response = github_client.append_to_file(
            file_path,
            content.strip(),
            str(commit_message).strip() or "Update notes via Genie",
        )
        return _translate_github_response(response, locale)

    if localized:
        return localized["unknown"]
    return (
        "Не удалось распознать команду. Попробуйте, например: «покажи задачи» "
        "или «добавь в файл notes.md купить молоко»."
    )


class AssistantService:
    """Connected assistant session with one GitHub client and intent parser."""

    def __init__(self, github_client: GitHubOperations, intent_parser: Any):
        self.github_client = github_client
        self.intent_parser = intent_parser

    @classmethod
    def from_config(cls) -> AssistantService:
        Config.reload()
        Config.validate(require_github=True)

        from github_service.client import GitHubClient
        from github_service.intents import IntentParser

        github_client = GitHubClient(
            Config.GITHUB_TOKEN,
            Config.GITHUB_REPO,
            branch=Config.GITHUB_BRANCH,
        )
        if not github_client.verify_main_branch():
            github_client.close()
            raise RuntimeError("В репозитории не найдена обязательная ветка main.")

        provider = Config.provider_settings()
        compatible = provider["provider"] in {"openai", "groq", "local", "custom"}
        intent_key = provider["key"] or (
            "ollama-local" if provider["provider"] == "local" else ""
        )
        try:
            parser = IntentParser(
                intent_key if compatible else "",
                provider["base_url"] if compatible else Config.OPENAI_BASE_URL,
                model=provider["model"] if compatible else Config.OPENAI_MODEL,
            )
        except Exception:
            github_client.close()
            raise
        return cls(github_client, parser)

    def execute_text(
        self, text: str, language: str = "ru"
    ) -> tuple[dict[str, Any], str]:
        text = text.strip()
        if not text:
            raise ValueError("Введите команду.")
        if len(text) > 4000:
            raise ValueError("Команда слишком длинная (максимум 4000 символов).")
        intent = self.intent_parser.parse_intent(text)
        response = execute_intent(intent, self.github_client, language=language)
        return intent, response

    def execute_action(
        self, action: str, language: str = "ru"
    ) -> tuple[dict[str, Any], str]:
        allowed = {
            "check_notifications",
            "check_issues",
            "check_prs",
            "check_actions",
            "recent_commits",
        }
        if action not in allowed:
            raise ValueError("Неизвестное быстрое действие.")
        intent = {"action": action}
        return intent, execute_intent(intent, self.github_client, language=language)

    def close(self) -> None:
        close = getattr(self.github_client, "close", None)
        if callable(close):
            close()

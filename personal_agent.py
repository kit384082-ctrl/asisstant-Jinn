"""Local personal-assistant tools: agenda, reminders and application launching."""

from __future__ import annotations

import base64
import logging
import math
import os
import platform
import re
import shutil
import sqlite3
import subprocess
import threading
import webbrowser
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any, ClassVar

logger = logging.getLogger(__name__)
UTC = timezone.utc


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _utc_string(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _parse_datetime(value: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise TypeError("Дата и время должны быть строкой в формате ISO.")
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Некорректные дата и время.") from exc
    if parsed.tzinfo is None:
        parsed = parsed.astimezone()
    return parsed.astimezone(UTC)


def _clean_text(value: Any, field: str, maximum: int) -> str:
    if not isinstance(value, str):
        raise TypeError(f"Поле «{field}» должно быть строкой.")
    cleaned = " ".join(value.strip().split())
    if not cleaned:
        raise ValueError(f"Заполните поле «{field}».")
    if len(cleaned) > maximum:
        raise ValueError(f"Поле «{field}» слишком длинное (максимум {maximum}).")
    return cleaned


class AgendaStore:
    """Small SQLite store safe to use from the threaded HTTP server."""

    ITEM_KINDS = frozenset({"timer", "reminder", "event", "note"})

    def __init__(self, database_path: Path | str):
        self.path = Path(database_path).expanduser().resolve()
        parent_was_missing = not self.path.parent.exists()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            # Do not unexpectedly change permissions on a user-selected existing
            # directory such as Documents. Directories created for Genie are private.
            if parent_was_missing:
                self.path.parent.chmod(0o700)
        except OSError:
            logger.debug(
                "Could not restrict the personal-data directory", exc_info=True
            )
        self._initialize()
        self._restrict_data_files()

    def _restrict_data_files(self) -> None:
        for candidate in (
            self.path,
            Path(f"{self.path}-wal"),
            Path(f"{self.path}-shm"),
        ):
            try:
                if candidate.exists():
                    candidate.chmod(0o600)
            except OSError:
                logger.debug("Could not restrict a personal-data file", exc_info=True)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            # WAL/SHM files may exist only while this connection is open. Restrict
            # them before close as well as afterwards in case SQLite keeps them.
            self._restrict_data_files()
            connection.close()
            self._restrict_data_files()

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                PRAGMA journal_mode = WAL;
                CREATE TABLE IF NOT EXISTS items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kind TEXT NOT NULL CHECK(kind IN ('timer', 'reminder', 'event', 'note')),
                    title TEXT NOT NULL,
                    details TEXT NOT NULL DEFAULT '',
                    due_at TEXT,
                    created_at TEXT NOT NULL,
                    notified_at TEXT,
                    completed_at TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_items_due
                    ON items(completed_at, due_at);
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_id INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
                    title TEXT NOT NULL,
                    body TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    alias TEXT NOT NULL UNIQUE,
                    executable TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )

    @staticmethod
    def _item(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "kind": row["kind"],
            "title": row["title"],
            "details": row["details"],
            "due_at": row["due_at"],
            "created_at": row["created_at"],
            "notified_at": row["notified_at"],
            "completed_at": row["completed_at"],
        }

    def create_item(
        self,
        kind: str,
        title: str,
        *,
        details: str = "",
        due_at: datetime | None = None,
    ) -> dict[str, Any]:
        if kind not in self.ITEM_KINDS:
            raise ValueError("Неизвестный тип записи.")
        clean_title = _clean_text(title, "Название", 160)
        if not isinstance(details, str):
            raise TypeError("Описание должно быть строкой.")
        clean_details = details.strip()
        if len(clean_details) > 4000:
            raise ValueError("Описание слишком длинное (максимум 4000 символов).")
        if kind != "note" and due_at is None:
            raise ValueError("Укажите дату или длительность.")
        due_value = _utc_string(due_at) if due_at is not None else None
        created = _utc_string(_utc_now())
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO items(kind, title, details, due_at, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (kind, clean_title, clean_details, due_value, created),
            )
            row = connection.execute(
                "SELECT * FROM items WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
        if row is None:
            raise RuntimeError("Не удалось прочитать созданную запись.")
        return self._item(row)

    def list_items(
        self,
        *,
        kind: str | None = None,
        include_completed: bool = False,
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        if kind is not None and kind not in self.ITEM_KINDS:
            raise ValueError("Неизвестный тип записей.")
        limit = max(1, min(int(limit), 1000))
        clauses: list[str] = []
        values: list[Any] = []
        if not include_completed:
            clauses.append("completed_at IS NULL")
        if kind:
            clauses.append("kind = ?")
            values.append(kind)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        values.append(limit)
        # `where` contains only fixed clauses selected above; values remain bound.
        query = f"""
            SELECT * FROM items
            {where}
            ORDER BY
                CASE WHEN due_at IS NULL THEN 1 ELSE 0 END,
                due_at ASC,
                created_at DESC
            LIMIT ?
        """  # noqa: S608
        with self._connect() as connection:
            rows = connection.execute(query, values).fetchall()
        return [self._item(row) for row in rows]

    def get_item(self, item_id: int) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM items WHERE id = ?", (item_id,)
            ).fetchone()
        if row is None:
            raise ValueError("Запись не найдена.")
        return self._item(row)

    def complete_item(self, item_id: int) -> dict[str, Any]:
        completed = _utc_string(_utc_now())
        with self._connect() as connection:
            cursor = connection.execute(
                "UPDATE items SET completed_at = ? WHERE id = ? AND completed_at IS NULL",
                (completed, item_id),
            )
            if cursor.rowcount == 0:
                raise ValueError("Активная запись не найдена.")
        return self.get_item(item_id)

    def delete_item(self, item_id: int) -> None:
        with self._connect() as connection:
            cursor = connection.execute("DELETE FROM items WHERE id = ?", (item_id,))
            if cursor.rowcount == 0:
                raise ValueError("Запись не найдена.")

    def collect_due(self, language: str = "ru") -> list[dict[str, Any]]:
        now = _utc_string(_utc_now())
        locale = language.split("-", 1)[0].casefold()
        labels_by_language = {
            "ru": {
                "timer": "Таймер завершён",
                "reminder": "Напоминание",
                "event": "Событие начинается",
                "note": "Заметка",
            },
            "en": {
                "timer": "Timer finished",
                "reminder": "Reminder",
                "event": "Event starting",
                "note": "Note",
            },
            "de": {
                "timer": "Timer beendet",
                "reminder": "Erinnerung",
                "event": "Termin beginnt",
                "note": "Notiz",
            },
            "es": {
                "timer": "Temporizador finalizado",
                "reminder": "Recordatorio",
                "event": "El evento comienza",
                "note": "Nota",
            },
            "fr": {
                "timer": "Minuteur terminé",
                "reminder": "Rappel",
                "event": "L’événement commence",
                "note": "Note",
            },
        }
        labels = labels_by_language.get(locale, labels_by_language["ru"])
        created_notifications: list[dict[str, Any]] = []
        with self._connect() as connection:
            # GET polling and the scheduler can arrive together. An immediate
            # transaction makes claiming due rows atomic and prevents duplicate
            # notifications from concurrent connections.
            connection.execute("BEGIN IMMEDIATE")
            rows = connection.execute(
                """
                SELECT * FROM items
                WHERE completed_at IS NULL
                  AND notified_at IS NULL
                  AND due_at IS NOT NULL
                  AND due_at <= ?
                ORDER BY due_at ASC
                """,
                (now,),
            ).fetchall()
            for row in rows:
                title = labels[row["kind"]]
                body = row["title"]
                cursor = connection.execute(
                    """
                    INSERT INTO notifications(item_id, title, body, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (row["id"], title, body, now),
                )
                connection.execute(
                    "UPDATE items SET notified_at = ? WHERE id = ?",
                    (now, row["id"]),
                )
                created_notifications.append(
                    {
                        "id": cursor.lastrowid,
                        "item_id": row["id"],
                        "kind": row["kind"],
                        "title": title,
                        "body": body,
                        "created_at": now,
                    }
                )
        return created_notifications

    def list_notifications(self, after_id: int = 0) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT notifications.id, notifications.item_id, items.kind,
                       notifications.title, notifications.body, notifications.created_at
                FROM notifications
                JOIN items ON items.id = notifications.item_id
                WHERE notifications.id > ?
                ORDER BY notifications.id ASC
                LIMIT 100
                """,
                (max(0, after_id),),
            ).fetchall()
        return [dict(row) for row in rows]

    def save_application(
        self, name: str, alias: str, executable: str
    ) -> dict[str, Any]:
        created = _utc_string(_utc_now())
        try:
            with self._connect() as connection:
                cursor = connection.execute(
                    """
                    INSERT INTO applications(name, alias, executable, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (name, alias, executable, created),
                )
                row = connection.execute(
                    "SELECT * FROM applications WHERE id = ?", (cursor.lastrowid,)
                ).fetchone()
        except sqlite3.IntegrityError as exc:
            raise ValueError("Приложение с таким названием уже добавлено.") from exc
        if row is None:
            raise RuntimeError("Не удалось прочитать созданное приложение.")
        return dict(row)

    def list_applications(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM applications ORDER BY name COLLATE NOCASE"
            ).fetchall()
        return [dict(row) for row in rows]

    def delete_application(self, app_id: int) -> None:
        with self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM applications WHERE id = ?", (app_id,)
            )
            if cursor.rowcount == 0:
                raise ValueError("Приложение не найдено.")


class DesktopNotifier:
    """Best-effort native notifications without shell interpolation."""

    @staticmethod
    def _windows_script(title: str, message: str) -> str:
        """Build a toast script containing only base64-encoded user text."""

        encoded_title = base64.b64encode(title.encode("utf-8")).decode("ascii")
        encoded_message = base64.b64encode(message.encode("utf-8")).decode("ascii")
        return f"""
$title = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('{encoded_title}'))
$message = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('{encoded_message}'))
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null
$template = [Windows.UI.Notifications.ToastTemplateType]::ToastText02
$xml = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent($template)
$nodes = $xml.GetElementsByTagName('text')
$nodes.Item(0).AppendChild($xml.CreateTextNode($title)) > $null
$nodes.Item(1).AppendChild($xml.CreateTextNode($message)) > $null
$toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('Genie Assistant').Show($toast)
""".strip()

    def send(self, title: str, message: str) -> bool:
        system = platform.system()
        try:
            if system == "Windows":
                powershell = shutil.which("powershell.exe") or shutil.which("pwsh.exe")
                if powershell:
                    encoded_script = base64.b64encode(
                        self._windows_script(title, message).encode("utf-16-le")
                    ).decode("ascii")
                    options: dict[str, Any] = {}
                    if hasattr(subprocess, "CREATE_NO_WINDOW"):
                        options["creationflags"] = subprocess.CREATE_NO_WINDOW
                    # Executable comes from shutil.which; arguments are fixed/encoded.
                    subprocess.Popen(  # noqa: S603
                        [
                            powershell,
                            "-NoProfile",
                            "-NonInteractive",
                            "-ExecutionPolicy",
                            "Bypass",
                            "-EncodedCommand",
                            encoded_script,
                        ],
                        stdin=subprocess.DEVNULL,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        **options,
                    )
                    return True
            notify_send = shutil.which("notify-send") if system == "Linux" else None
            if notify_send:
                subprocess.Popen(  # noqa: S603 - resolved executable, argument array.
                    [notify_send, title, message],
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                return True
            osascript = shutil.which("osascript") if system == "Darwin" else None
            if osascript:
                script = (
                    "on run argv\n"
                    "display notification (item 2 of argv) with title (item 1 of argv)\n"
                    "end run"
                )
                subprocess.Popen(  # noqa: S603 - resolved executable, argument array.
                    [osascript, "-e", script, title, message],
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                return True
        except (OSError, ValueError):
            logger.debug("Native notification failed", exc_info=True)
        return False


class AppLauncher:
    """Cross-platform allowlisted application launcher with no shell execution."""

    BUILTIN_APPS = (
        {"alias": "browser", "name": "Браузер", "icon": "globe", "accent": "violet"},
        {"alias": "files", "name": "Файлы", "icon": "folder", "accent": "amber"},
        {"alias": "terminal", "name": "Терминал", "icon": "terminal", "accent": "cyan"},
        {
            "alias": "calculator",
            "name": "Калькулятор",
            "icon": "calculator",
            "accent": "green",
        },
        {"alias": "editor", "name": "Редактор", "icon": "edit", "accent": "rose"},
        {
            "alias": "vscode",
            "name": "Visual Studio Code",
            "icon": "code",
            "accent": "blue",
        },
        {"alias": "telegram", "name": "Telegram", "icon": "send", "accent": "cyan"},
        {"alias": "discord", "name": "Discord", "icon": "message", "accent": "violet"},
    )
    ALIASES: ClassVar[dict[str, str]] = {
        "браузер": "browser",
        "интернет": "browser",
        "browser": "browser",
        "navegador": "browser",
        "navigateur": "browser",
        "internetbrowser": "browser",
        "файлы": "files",
        "проводник": "files",
        "finder": "files",
        "files": "files",
        "dateien": "files",
        "explorer": "files",
        "archivos": "files",
        "fichiers": "files",
        "терминал": "terminal",
        "консоль": "terminal",
        "terminal": "terminal",
        "konsole": "terminal",
        "consola": "terminal",
        "калькулятор": "calculator",
        "calculator": "calculator",
        "rechner": "calculator",
        "calculadora": "calculator",
        "calculatrice": "calculator",
        "редактор": "editor",
        "блокнот": "editor",
        "textedit": "editor",
        "editor": "editor",
        "éditeur": "editor",
        "editeur": "editor",
        "vs code": "vscode",
        "vscode": "vscode",
        "visual studio code": "vscode",
        "телеграм": "telegram",
        "telegram": "telegram",
        "дискорд": "discord",
        "discord": "discord",
    }

    def __init__(self, store: AgendaStore):
        self.store = store

    @staticmethod
    def _first_available(commands: tuple[str, ...]) -> str | None:
        for command in commands:
            found = shutil.which(command)
            if found:
                return found
        return None

    @staticmethod
    def _first_existing(paths: tuple[Path, ...]) -> str | None:
        return next((str(path) for path in paths if path.is_file()), None)

    @staticmethod
    def _environment_root(name: str, fallback: str = "") -> Path | None:
        value = os.getenv(name, fallback).strip()
        if not value:
            return None
        candidate = Path(value)
        return candidate if candidate.is_absolute() else None

    def _builtin_command(self, alias: str) -> list[str] | None:
        system = platform.system()
        home = str(Path.home())
        if alias == "browser":
            return ["__webbrowser__"]
        if system == "Windows":
            windows = self._environment_root("WINDIR", r"C:\Windows")
            local = self._environment_root("LOCALAPPDATA")
            roaming = self._environment_root("APPDATA")
            program_files = self._environment_root("ProgramFiles")
            program_files_x86 = self._environment_root("ProgramFiles(x86)")
            if windows is None:
                return None
            standard = {
                "files": windows / "explorer.exe",
                "terminal": windows / "System32" / "cmd.exe",
                "calculator": windows / "System32" / "calc.exe",
                "editor": windows / "System32" / "notepad.exe",
            }
            if alias in standard:
                executable = standard[alias]
                if not executable.is_file():
                    return None
                return (
                    [str(executable), home] if alias == "files" else [str(executable)]
                )
            vscode_paths = (
                local / "Programs" / "Microsoft VS Code" / "Code.exe"
                if local is not None
                else None,
                program_files / "Microsoft VS Code" / "Code.exe"
                if program_files is not None
                else None,
                program_files_x86 / "Microsoft VS Code" / "Code.exe"
                if program_files_x86 is not None
                else None,
            )
            candidates = {
                "vscode": tuple(path for path in vscode_paths if path is not None),
                "telegram": (
                    (roaming / "Telegram Desktop" / "Telegram.exe",)
                    if roaming is not None
                    else ()
                ),
                "discord": (
                    tuple(
                        sorted(
                            (local / "Discord").glob("app-*/Discord.exe"),
                            reverse=True,
                        )
                    )
                    if local is not None
                    else ()
                ),
            }
            executable = self._first_existing(candidates.get(alias, ()))
            return [executable] if executable else None
        if system == "Darwin":
            applications = {
                "files": ("Finder", Path("/System/Library/CoreServices/Finder.app")),
                "terminal": (
                    "Terminal",
                    Path("/System/Applications/Utilities/Terminal.app"),
                ),
                "calculator": (
                    "Calculator",
                    Path("/System/Applications/Calculator.app"),
                ),
                "editor": ("TextEdit", Path("/System/Applications/TextEdit.app")),
                "vscode": (
                    "Visual Studio Code",
                    Path("/Applications/Visual Studio Code.app"),
                ),
                "telegram": ("Telegram", Path("/Applications/Telegram.app")),
                "discord": ("Discord", Path("/Applications/Discord.app")),
            }
            definition = applications.get(alias)
            if not definition or not definition[1].is_dir() or not shutil.which("open"):
                return None
            return ["open", "-a", definition[0]]

        candidates = {
            "files": ("xdg-open",),
            "terminal": ("x-terminal-emulator", "gnome-terminal", "konsole", "xterm"),
            "calculator": ("gnome-calculator", "kcalc", "galculator"),
            "editor": ("gedit", "kate", "mousepad", "xed"),
            "vscode": ("code", "code-insiders"),
            "telegram": ("telegram-desktop", "telegram"),
            "discord": ("discord",),
        }
        command = self._first_available(candidates.get(alias, ()))
        if not command:
            return None
        return [command, home] if alias == "files" else [command]

    def list_apps(self) -> list[dict[str, Any]]:
        apps: list[dict[str, Any]] = []
        for definition in self.BUILTIN_APPS:
            command = self._builtin_command(definition["alias"])
            apps.append(
                {
                    **definition,
                    "builtin": True,
                    "available": command is not None,
                }
            )
        for custom in self.store.list_applications():
            apps.append(
                {
                    "id": custom["id"],
                    "alias": custom["alias"],
                    "name": custom["name"],
                    "icon": "app",
                    "accent": "custom",
                    "builtin": False,
                    "available": self._custom_command(Path(custom["executable"]))
                    is not None,
                }
            )
        return apps

    @staticmethod
    def _custom_command(candidate: Path) -> list[str] | None:
        system = platform.system()
        if (
            system == "Darwin"
            and candidate.is_dir()
            and candidate.suffix.casefold() == ".app"
            and shutil.which("open")
        ):
            return ["open", str(candidate)]
        if not candidate.is_file():
            return None
        if system == "Windows":
            if candidate.suffix.casefold() not in {".exe", ".com"}:
                return None
        elif not os.access(candidate, os.X_OK):
            return None
        return [str(candidate)]

    @staticmethod
    def _normalize_alias(name: str) -> str:
        normalized_name = name.casefold().replace("ё", "е")
        alias = re.sub(r"[^\w-]+", "-", normalized_name, flags=re.UNICODE).strip("-")
        if not alias:
            raise ValueError("Не удалось создать имя приложения.")
        return alias[:64]

    def register(self, name: str, executable: str) -> dict[str, Any]:
        clean_name = _clean_text(name, "Название", 60)
        if not isinstance(executable, str):
            raise TypeError("Путь к приложению должен быть строкой.")
        raw_path = os.path.expandvars(executable.strip())
        if not raw_path:
            raise ValueError("Укажите путь к приложению.")
        candidate = Path(raw_path).expanduser()
        if not candidate.is_absolute():
            raise ValueError("Укажите абсолютный путь к исполняемому файлу.")
        candidate = candidate.resolve()
        if not candidate.exists():
            raise ValueError("Исполняемый файл не найден.")
        if self._custom_command(candidate) is None:
            raise ValueError(
                "Указанный путь не является поддерживаемым исполняемым файлом."
            )
        alias = self._normalize_alias(clean_name)
        reserved = {app["alias"] for app in self.BUILTIN_APPS} | {
            self._normalize_alias(synonym) for synonym in self.ALIASES
        }
        if alias in reserved:
            raise ValueError("Это название зарезервировано системным приложением.")
        saved = self.store.save_application(clean_name, alias, str(candidate))
        return {
            "id": saved["id"],
            "name": saved["name"],
            "alias": saved["alias"],
            "builtin": False,
            "available": True,
            "icon": "app",
            "accent": "custom",
        }

    @staticmethod
    def _spawn(command: list[str]) -> None:
        options: dict[str, Any] = {
            "stdin": subprocess.DEVNULL,
            "stdout": subprocess.DEVNULL,
            "stderr": subprocess.DEVNULL,
            "close_fds": True,
        }
        if os.name == "posix":
            options["start_new_session"] = True
        # Commands are resolved from built-ins or validated registered executables.
        subprocess.Popen(command, **options)  # noqa: S603

    def launch(self, requested_alias: str) -> str:
        if not isinstance(requested_alias, str):
            raise TypeError("Название приложения должно быть строкой.")
        normalized = " ".join(requested_alias.casefold().replace("ё", "е").split())
        normalized = re.sub(
            r"^(?:приложение|app|anwendung|aplicación|aplicacion|application)\s+",
            "",
            normalized,
        )
        alias = self.ALIASES.get(normalized, self._normalize_alias(normalized))
        builtins = {app["alias"]: app for app in self.BUILTIN_APPS}
        if alias in builtins:
            command = self._builtin_command(alias)
            if command is None:
                raise ValueError(
                    f"Приложение «{builtins[alias]['name']}» не найдено в системе."
                )
            if command == ["__webbrowser__"]:
                if not webbrowser.open("about:blank"):
                    raise RuntimeError("Не удалось открыть браузер.")
            else:
                self._spawn(command)
            return builtins[alias]["name"]

        custom = next(
            (app for app in self.store.list_applications() if app["alias"] == alias),
            None,
        )
        if custom is None:
            raise ValueError(
                "Приложение не найдено. Добавьте его в разделе «Приложения»."
            )
        executable = Path(custom["executable"])
        command = self._custom_command(executable)
        if command is None:
            raise ValueError(
                "Сохранённый путь больше не ведёт к поддерживаемому исполняемому файлу."
            )
        self._spawn(command)
        return custom["name"]


class PersonalAgent:
    """Command router and scheduler for local personal-assistant actions."""

    def __init__(
        self,
        database_path: Path | str,
        *,
        start_scheduler: bool = True,
        notifier: DesktopNotifier | None = None,
        language: str = "ru",
    ):
        self.store = AgendaStore(database_path)
        self.launcher = AppLauncher(self.store)
        self.notifier = notifier or DesktopNotifier()
        self.language = "ru"
        self.set_language(language)
        self._stop_event = threading.Event()
        self._scheduler: threading.Thread | None = None
        if start_scheduler:
            self._scheduler = threading.Thread(
                target=self._scheduler_loop,
                name="genie-reminder-scheduler",
                daemon=True,
            )
            self._scheduler.start()

    def set_language(self, language: str) -> None:
        code = language.split("-", 1)[0].casefold()
        self.language = code if code in {"ru", "en", "de", "es", "fr"} else "ru"

    def _scheduler_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self.process_due_notifications()
            except Exception:
                logger.exception("Reminder scheduler failed")
            self._stop_event.wait(1.0)

    def process_due_notifications(self) -> list[dict[str, Any]]:
        notifications = self.store.collect_due(language=self.language)
        for notification in notifications:
            self.notifier.send(notification["title"], notification["body"])
        return notifications

    def create_timer(
        self, duration_seconds: Any, label: str = "Таймер"
    ) -> dict[str, Any]:
        if isinstance(duration_seconds, bool):
            raise TypeError("Длительность должна быть числом.")
        try:
            duration = int(duration_seconds)
        except (TypeError, ValueError) as exc:
            raise TypeError("Длительность должна быть целым числом секунд.") from exc
        if not 1 <= duration <= 31 * 24 * 60 * 60:
            raise ValueError("Таймер может длиться от 1 секунды до 31 дня.")
        return self.store.create_item(
            "timer",
            label or "Таймер",
            details=str(duration),
            due_at=_utc_now() + timedelta(seconds=duration),
        )

    def create_reminder(
        self, title: str, due_at: str, details: str = ""
    ) -> dict[str, Any]:
        due = _parse_datetime(due_at)
        if due < _utc_now() - timedelta(seconds=5):
            raise ValueError("Напоминание нельзя поставить в прошлом.")
        return self.store.create_item("reminder", title, details=details, due_at=due)

    def create_event(
        self, title: str, due_at: str, details: str = ""
    ) -> dict[str, Any]:
        return self.store.create_item(
            "event", title, details=details, due_at=_parse_datetime(due_at)
        )

    def create_note(self, title: str, details: str = "") -> dict[str, Any]:
        return self.store.create_item("note", title, details=details)

    def summary(self) -> dict[str, Any]:
        items = self.store.list_items(limit=500)
        counts = {kind: 0 for kind in AgendaStore.ITEM_KINDS}
        for item in items:
            counts[item["kind"]] += 1
        upcoming = [item for item in items if item["due_at"] is not None]
        return {
            "counts": counts,
            "next_item": upcoming[0] if upcoming else None,
            "scheduler_running": bool(self._scheduler and self._scheduler.is_alive()),
            "platform": platform.system(),
        }

    @staticmethod
    def _parse_duration(text: str) -> tuple[int, str] | None:
        units = {
            "сек": 1,
            "second": 1,
            "sekund": 1,
            "segundo": 1,
            "seconde": 1,
            "мин": 60,
            "minute": 60,
            "minuto": 60,
            "час": 3600,
            "hour": 3600,
            "stund": 3600,
            "hora": 3600,
            "heure": 3600,
            "день": 86400,
            "дня": 86400,
            "дней": 86400,
            "day": 86400,
            "tag": 86400,
            "tage": 86400,
            "día": 86400,
            "dia": 86400,
            "jour": 86400,
        }
        pattern = re.compile(
            r"(\d+(?:[.,]\d+)?)\s*"
            r"(секунд(?:у|ы)?|сек|seconds?|sekunden?|segundos?|secondes?|"
            r"минут(?:у|ы)?|мин|minutes?|minuten?|minutos?|"
            r"час(?:а|ов)?|hours?|stunden?|horas?|heures?|"
            r"д(?:ень|ня|ней)|days?|tage?n?|d[ií]as?|jours?)\b",
            re.IGNORECASE,
        )
        total = 0.0
        matches: list[str] = []
        for match in pattern.finditer(text):
            number = float(match.group(1).replace(",", "."))
            if not math.isfinite(number):
                raise ValueError("Указана слишком большая длительность.")
            unit_text = match.group(2).casefold()
            multiplier = next(
                (
                    value
                    for prefix, value in units.items()
                    if unit_text.startswith(prefix)
                ),
                None,
            )
            if multiplier:
                total += number * multiplier
                if not math.isfinite(total):
                    raise ValueError("Указана слишком большая длительность.")
                matches.append(match.group(0))
        if not matches or total < 1:
            return None
        return int(total), " ".join(matches)

    @classmethod
    def is_timer_command(cls, text: str, language: str = "ru") -> bool:
        """Recognize timer syntax without executing it.

        The HTTP boundary uses this to distinguish ambiguous localized verbs such
        as “start” or “lance” from application-launch requests.
        """

        if not isinstance(text, str):
            return False
        lowered = " ".join(text.casefold().replace("ё", "е").split())
        if not lowered or cls._parse_duration(lowered) is None:
            return False
        locale = language.split("-", 1)[0].casefold()
        if locale in cls._LOCAL_COMMANDS:
            pack = cls._LOCAL_COMMANDS[locale]
            return any(noun in lowered for noun in pack["timer_nouns"]) and any(
                verb in lowered for verb in pack["timer_verbs"]
            )
        return "таймер" in lowered and bool(
            re.search(r"\b(?:постав|установ|запуст|созда)\w*", lowered)
            or re.match(r"^таймер\b", lowered)
        )

    @staticmethod
    def _extract_due(text: str) -> tuple[datetime, str] | None:
        lowered = text.casefold().replace("ё", "е")
        now = datetime.now().astimezone()
        target_date: date | None = None
        date_fragment = ""
        relative_days = {
            "послезавтра": 2,
            "day after tomorrow": 2,
            "übermorgen": 2,
            "pasado mañana": 2,
            "après-demain": 2,
            "завтра": 1,
            "tomorrow": 1,
            "morgen": 1,
            "mañana": 1,
            "demain": 1,
            "сегодня": 0,
            "today": 0,
            "heute": 0,
            "hoy": 0,
            "aujourd'hui": 0,
        }
        for word, offset in relative_days.items():
            if word in lowered:
                target_date = (now + timedelta(days=offset)).date()
                date_fragment = word
                break

        if target_date is None:
            iso_match = re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b", lowered)
            dot_match = re.search(r"\b(\d{1,2})[.](\d{1,2})(?:[.](\d{4}))?\b", lowered)
            try:
                if iso_match:
                    target_date = date(*map(int, iso_match.groups()))
                    date_fragment = iso_match.group(0)
                elif dot_match:
                    day, month, year = dot_match.groups()
                    target_date = date(int(year or now.year), int(month), int(day))
                    date_fragment = dot_match.group(0)
            except ValueError as exc:
                raise ValueError("Некорректная дата в команде.") from exc

        time_match = re.search(
            r"(?:(?:\bв|\bна|\bat|\bum|\ba\s+las|\bà)\s+)?"
            r"([01]?\d|2[0-3])[:.]([0-5]\d)\b",
            lowered,
        )
        if not time_match and target_date is not None:
            time_match = re.search(
                r"(?:\bв|\bat|\bum|\ba\s+las|\bà)\s+([01]?\d|2[0-3])\b",
                lowered,
            )
        if target_date is None and time_match is None:
            return None
        hour = int(time_match.group(1)) if time_match else 9
        minute = (
            int(time_match.group(2)) if time_match and time_match.lastindex == 2 else 0
        )
        target_date = target_date or now.date()
        due = datetime.combine(target_date, time(hour, minute), tzinfo=now.tzinfo)
        if date_fragment == "" and due <= now:
            due += timedelta(days=1)
        fragments = " ".join(
            fragment
            for fragment in (date_fragment, time_match.group(0) if time_match else "")
            if fragment
        )
        return due.astimezone(UTC), fragments

    @staticmethod
    def _strip_command_parts(text: str, *parts: str) -> str:
        result = text
        for part in parts:
            if part:
                result = re.sub(
                    re.escape(part), " ", result, count=1, flags=re.IGNORECASE
                )
        result = re.sub(
            r"^\s*(?:пожалуйста[,.]?\s*)?(?:мне\s+)?(?:на\s+|через\s+)?",
            "",
            result,
            flags=re.IGNORECASE,
        )
        return " ".join(result.strip(" ,.—–:-").split())

    _LOCAL_COMMANDS: ClassVar[dict[str, dict[str, Any]]] = {
        "en": {
            "open": r"^(?:please[,.]?\s*)?(?:open|launch|start)\s+(.+)$",
            "timer_nouns": ("timer",),
            "timer_verbs": ("set", "start", "create"),
            "reminder": r"^(?:please[,.]?\s*)?remind me(?:\s+to)?\s+(.+)$",
            "relative": ("in ",),
            "event_words": ("calendar", "event", "meeting"),
            "event_verbs": ("add", "create", "schedule"),
            "note": r"^(?:create|add|save|write)?\s*(?:a\s+)?note\s*[:—-]?\s*(.+)$",
            "complete": ("complete", "finish", "mark"),
            "delete": ("delete", "remove", "cancel"),
            "list": ("show", "list", "what", "which"),
            "kind_words": {
                "timer": ("timer",),
                "reminder": ("reminder",),
                "event": ("event", "calendar", "plan"),
                "note": ("note",),
            },
            "greetings": (
                "hello",
                "hi",
                "good morning",
                "good afternoon",
                "good evening",
            ),
            "help": ("what can you do", "help", "commands"),
            "time": ("what time", "current time"),
            "labels": {
                "timer": "Timer",
                "reminder": "Reminder",
                "event": "Event",
                "note": "Note",
            },
            "timer_need": "Specify a duration, for example “for 10 minutes”.",
            "timer_done": "Timer “{title}” set for {duration}.",
            "reminder_need": "Specify a time, such as “in 20 minutes” or “tomorrow at 09:00”.",
            "reminder_done": "Okay, I’ll remind you: “{title}”.",
            "event_need": "Specify the event date and time.",
            "event_done": "Event “{title}” was added to the calendar.",
            "note_done": "Note saved: “{title}”.",
            "complete_done": "Item #{id} marked complete.",
            "delete_done": "Item #{id} deleted.",
            "none": {
                "timer": "active timers",
                "reminder": "reminders",
                "event": "events",
                "note": "notes",
            },
            "greeting": "Hello! I can set timers and reminders, add events, save notes or open an application.",
            "help_response": "I manage timers, reminders, calendar, notes, applications and GitHub. Try: “remind me to call in 20 minutes” or “open calculator”.",
            "time_response": "It is {time}.",
        },
        "de": {
            "open": r"^(?:bitte[,.]?\s*)?(?:öffne|oeffne|starte)\s+(.+)$",
            "timer_nouns": ("timer",),
            "timer_verbs": ("stelle", "starte", "erstelle"),
            "reminder": r"^(?:bitte[,.]?\s*)?erinnere mich(?:\s+daran)?\s+(.+)$",
            "relative": ("in ",),
            "event_words": ("kalender", "termin", "ereignis", "treffen"),
            "event_verbs": ("füge", "fuege", "erstelle", "plane"),
            "note": r"^(?:erstelle|füge|fuege|speichere|schreibe)?\s*(?:eine\s+)?notiz\s*[:—-]?\s*(.+)$",
            "complete": ("erledige", "beende", "markiere"),
            "delete": ("lösche", "loesche", "entferne", "storniere"),
            "list": ("zeige", "liste", "welche"),
            "kind_words": {
                "timer": ("timer",),
                "reminder": ("erinnerung",),
                "event": ("termin", "ereignis", "kalender", "plan"),
                "note": ("notiz",),
            },
            "greetings": ("hallo", "guten morgen", "guten tag", "guten abend"),
            "help": ("was kannst du", "hilfe", "befehle"),
            "time": ("wie spät", "aktuelle uhrzeit"),
            "labels": {
                "timer": "Timer",
                "reminder": "Erinnerung",
                "event": "Termin",
                "note": "Notiz",
            },
            "timer_need": "Gib eine Dauer an, zum Beispiel „10 Minuten“.",
            "timer_done": "Timer „{title}“ für {duration} gestellt.",
            "reminder_need": "Gib eine Zeit an, etwa „in 20 Minuten“ oder „morgen um 09:00“.",
            "reminder_done": "Okay, ich erinnere dich: „{title}“.",
            "event_need": "Gib Datum und Uhrzeit des Termins an.",
            "event_done": "Termin „{title}“ wurde zum Kalender hinzugefügt.",
            "note_done": "Notiz gespeichert: „{title}“.",
            "complete_done": "Eintrag #{id} als erledigt markiert.",
            "delete_done": "Eintrag #{id} gelöscht.",
            "none": {
                "timer": "aktiven Timer",
                "reminder": "Erinnerungen",
                "event": "Termine",
                "note": "Notizen",
            },
            "greeting": "Hallo! Ich kann Timer und Erinnerungen erstellen, Termine und Notizen speichern oder Anwendungen öffnen.",
            "help_response": "Ich verwalte Timer, Erinnerungen, Kalender, Notizen, Anwendungen und GitHub. Sage zum Beispiel: „Erinnere mich in 20 Minuten anzurufen“.",
            "time_response": "Es ist {time} Uhr.",
        },
        "es": {
            "open": r"^(?:por favor[,.]?\s*)?(?:abre|inicia|lanza)\s+(.+)$",
            "timer_nouns": ("temporizador",),
            "timer_verbs": ("pon", "configura", "inicia", "crea"),
            "reminder": r"^(?:por favor[,.]?\s*)?recuérdame(?:\s+que|\s+de)?\s+(.+)$",
            "relative": ("en ", "dentro de "),
            "event_words": ("calendario", "evento", "reunión", "reunion"),
            "event_verbs": ("añade", "anade", "crea", "programa"),
            "note": r"^(?:crea|añade|anade|guarda|escribe)?\s*(?:una\s+)?nota\s*[:—-]?\s*(.+)$",
            "complete": ("completa", "termina", "marca"),
            "delete": ("elimina", "borra", "cancela"),
            "list": ("muestra", "lista", "qué", "que", "cuáles", "cuales"),
            "kind_words": {
                "timer": ("temporizador",),
                "reminder": ("recordatorio",),
                "event": ("evento", "calendario", "plan"),
                "note": ("nota",),
            },
            "greetings": ("hola", "buenos días", "buenas tardes", "buenas noches"),
            "help": ("qué puedes hacer", "que puedes hacer", "ayuda", "comandos"),
            "time": ("qué hora", "que hora", "hora actual"),
            "labels": {
                "timer": "Temporizador",
                "reminder": "Recordatorio",
                "event": "Evento",
                "note": "Nota",
            },
            "timer_need": "Indica una duración, por ejemplo «10 minutos».",
            "timer_done": "Temporizador «{title}» configurado por {duration}.",
            "reminder_need": "Indica una hora, por ejemplo «en 20 minutos» o «mañana a las 09:00».",
            "reminder_done": "De acuerdo, te lo recordaré: «{title}».",
            "event_need": "Indica la fecha y hora del evento.",
            "event_done": "El evento «{title}» se añadió al calendario.",
            "note_done": "Nota guardada: «{title}».",
            "complete_done": "Elemento #{id} marcado como completado.",
            "delete_done": "Elemento #{id} eliminado.",
            "none": {
                "timer": "temporizadores activos",
                "reminder": "recordatorios",
                "event": "eventos",
                "note": "notas",
            },
            "greeting": "¡Hola! Puedo crear temporizadores y recordatorios, añadir eventos, guardar notas o abrir aplicaciones.",
            "help_response": "Gestiono temporizadores, recordatorios, calendario, notas, aplicaciones y GitHub. Prueba: «recuérdame llamar en 20 minutos».",
            "time_response": "Son las {time}.",
        },
        "fr": {
            "open": r"^(?:s'il vous plaît[,.]?\s*)?(?:ouvre|lance|démarre|demarre)\s+(.+)$",
            "timer_nouns": ("minuteur", "chronomètre", "chronometre"),
            "timer_verbs": ("mets", "règle", "regle", "lance", "crée", "cree"),
            "reminder": r"^(?:s'il vous plaît[,.]?\s*)?rappelle-moi(?:\s+de)?\s+(.+)$",
            "relative": ("dans ",),
            "event_words": (
                "calendrier",
                "événement",
                "evenement",
                "réunion",
                "reunion",
            ),
            "event_verbs": ("ajoute", "crée", "cree", "planifie"),
            "note": r"^(?:crée|cree|ajoute|enregistre|écris|ecris)?\s*(?:une\s+)?note\s*[:—-]?\s*(.+)$",
            "complete": ("termine", "complète", "complete", "marque"),
            "delete": ("supprime", "efface", "annule"),
            "list": ("montre", "liste", "quels", "quelles"),
            "kind_words": {
                "timer": ("minuteur",),
                "reminder": ("rappel",),
                "event": ("événement", "evenement", "calendrier", "programme"),
                "note": ("note",),
            },
            "greetings": ("bonjour", "salut", "bonsoir"),
            "help": ("que peux-tu faire", "aide", "commandes"),
            "time": ("quelle heure", "heure actuelle"),
            "labels": {
                "timer": "Minuteur",
                "reminder": "Rappel",
                "event": "Événement",
                "note": "Note",
            },
            "timer_need": "Indiquez une durée, par exemple «10 minutes».",
            "timer_done": "Minuteur «{title}» réglé pour {duration}.",
            "reminder_need": "Indiquez une heure, par exemple «dans 20 minutes» ou «demain à 09:00».",
            "reminder_done": "D’accord, je vous le rappellerai : «{title}».",
            "event_need": "Indiquez la date et l’heure de l’événement.",
            "event_done": "L’événement «{title}» a été ajouté au calendrier.",
            "note_done": "Note enregistrée : «{title}».",
            "complete_done": "Élément #{id} marqué comme terminé.",
            "delete_done": "Élément #{id} supprimé.",
            "none": {
                "timer": "minuteurs actifs",
                "reminder": "rappels",
                "event": "événements",
                "note": "notes",
            },
            "greeting": "Bonjour ! Je peux créer des minuteurs et rappels, ajouter des événements, enregistrer des notes ou ouvrir une application.",
            "help_response": "Je gère minuteurs, rappels, calendrier, notes, applications et GitHub. Essayez : «rappelle-moi d’appeler dans 20 minutes».",
            "time_response": "Il est {time}.",
        },
    }

    @staticmethod
    def _localized_title(text: str, parts: tuple[str, ...], fallback: str) -> str:
        title = text
        for part in parts:
            if part:
                title = re.sub(
                    re.escape(part), " ", title, count=1, flags=re.IGNORECASE
                )
        title = re.sub(
            r"^(?:please|bitte|por favor|s'il vous plaît)?\s*",
            "",
            title,
            flags=re.IGNORECASE,
        )
        filler_words = {
            "a",
            "an",
            "the",
            "to",
            "for",
            "in",
            "at",
            "ein",
            "eine",
            "einen",
            "einem",
            "einer",
            "für",
            "um",
            "un",
            "una",
            "el",
            "la",
            "en",
            "de",
            "para",
            "une",
            "le",
            "les",
            "dans",
            "à",
            "pour",
            "que",
        }
        words = title.strip(" ,.—–:-").split()
        while words and words[0].casefold() in filler_words:
            words.pop(0)
        while words and words[-1].casefold() in filler_words:
            words.pop()
        return " ".join(words) or fallback

    def _try_execute_localized(
        self, original: str, language: str, *, allow_app_launch: bool = True
    ) -> dict[str, Any] | None:
        pack = self._LOCAL_COMMANDS[language]
        lowered = original.casefold()

        if any(noun in lowered for noun in pack["timer_nouns"]) and any(
            verb in lowered for verb in pack["timer_verbs"]
        ):
            duration = self._parse_duration(lowered)
            if not duration:
                raise ValueError(pack["timer_need"])
            noun = next(word for word in pack["timer_nouns"] if word in lowered)
            verb = next(word for word in pack["timer_verbs"] if word in lowered)
            title = self._localized_title(
                original, (verb, noun, duration[1]), pack["labels"]["timer"]
            )
            item = self.create_timer(duration[0], title)
            return {
                "intent": {"action": "create_timer", "item_id": item["id"]},
                "response": pack["timer_done"].format(
                    title=item["title"], duration=duration[1]
                ),
                "item": item,
            }

        # Some languages naturally use their generic “start” verb for timers
        # (for example, “Lance un minuteur”). Parse deterministic timer
        # commands before treating the same verb as an application launch.
        open_match = re.match(pack["open"], lowered, re.IGNORECASE)
        if open_match:
            if not allow_app_launch:
                raise PermissionError(
                    "Запуск приложений доступен только с этого компьютера."
                )
            name = self.launcher.launch(open_match.group(1))
            responses = {
                "en": f"Opening “{name}”.",
                "de": f"Ich öffne „{name}“.",
                "es": f"Abriendo «{name}».",
                "fr": f"J’ouvre «{name}».",
            }
            return {
                "intent": {"action": "open_app", "app": open_match.group(1)},
                "response": responses[language],
            }

        reminder_match = re.match(pack["reminder"], original, re.IGNORECASE)
        if reminder_match:
            remainder = reminder_match.group(1)
            duration = self._parse_duration(remainder)
            due: datetime | None = None
            fragment = ""
            if duration and any(
                marker in remainder.casefold() for marker in pack["relative"]
            ):
                due = _utc_now() + timedelta(seconds=duration[0])
                fragment = duration[1]
            else:
                extracted = self._extract_due(remainder)
                if extracted:
                    due, fragment = extracted
            if due is None:
                raise ValueError(pack["reminder_need"])
            title = self._localized_title(
                remainder,
                (fragment, *pack["relative"]),
                pack["labels"]["reminder"],
            )
            item = self.create_reminder(title, due.isoformat())
            return {
                "intent": {"action": "create_reminder", "item_id": item["id"]},
                "response": pack["reminder_done"].format(title=item["title"]),
                "item": item,
            }

        if any(word in lowered for word in pack["event_words"]) and any(
            verb in lowered for verb in pack["event_verbs"]
        ):
            extracted = self._extract_due(original)
            if not extracted:
                raise ValueError(pack["event_need"])
            due, fragment = extracted
            parts = (
                fragment,
                *(word for word in pack["event_words"] if word in lowered),
                *(word for word in pack["event_verbs"] if word in lowered),
            )
            title = self._localized_title(original, parts, pack["labels"]["event"])
            item = self.store.create_item("event", title, due_at=due)
            return {
                "intent": {"action": "create_event", "item_id": item["id"]},
                "response": pack["event_done"].format(title=item["title"]),
                "item": item,
            }

        note_match = re.match(pack["note"], original, re.IGNORECASE)
        if note_match:
            item = self.create_note(note_match.group(1))
            return {
                "intent": {"action": "create_note", "item_id": item["id"]},
                "response": pack["note_done"].format(title=item["title"]),
                "item": item,
            }

        identifier = re.search(r"#?(\d+)\s*$", lowered)
        if identifier and any(word in lowered for word in pack["complete"]):
            item_id = int(identifier.group(1))
            self.store.complete_item(item_id)
            return {
                "intent": {"action": "complete_item", "item_id": item_id},
                "response": pack["complete_done"].format(id=item_id),
            }
        if identifier and any(word in lowered for word in pack["delete"]):
            item_id = int(identifier.group(1))
            self.store.delete_item(item_id)
            return {
                "intent": {"action": "delete_item", "item_id": item_id},
                "response": pack["delete_done"].format(id=item_id),
            }

        if any(word in lowered for word in pack["list"]):
            for kind, words in pack["kind_words"].items():
                if any(word in lowered for word in words):
                    items = self.store.list_items(kind=kind, limit=5)
                    noun = pack["none"][kind]
                    responses = {
                        "en": f"There are no {noun} right now.",
                        "de": f"Derzeit gibt es keine {noun}.",
                        "es": f"Ahora no hay {noun}.",
                        "fr": f"Il n’y a actuellement aucun élément : {noun}.",
                    }
                    response = (
                        responses[language]
                        if not items
                        else f"{noun.capitalize()}: "
                        + "; ".join(f"#{item['id']} {item['title']}" for item in items)
                    )
                    return {
                        "intent": {"action": "list_items", "kind": kind},
                        "response": response,
                    }

        if any(lowered.startswith(greeting) for greeting in pack["greetings"]):
            return {"intent": {"action": "conversation"}, "response": pack["greeting"]}
        if any(phrase in lowered for phrase in pack["help"]):
            return {"intent": {"action": "help"}, "response": pack["help_response"]}
        if any(phrase in lowered for phrase in pack["time"]):
            return {
                "intent": {"action": "current_time"},
                "response": pack["time_response"].format(
                    time=f"{datetime.now().astimezone():%H:%M}"
                ),
            }
        return None

    def try_execute(
        self, text: str, language: str = "ru", *, allow_app_launch: bool = True
    ) -> dict[str, Any] | None:
        original = " ".join(text.strip().split())
        lowered = original.casefold().replace("ё", "е")
        locale = language.split("-", 1)[0].casefold()
        if locale in self._LOCAL_COMMANDS and original:
            result = self._try_execute_localized(
                original, locale, allow_app_launch=allow_app_launch
            )
            if result is not None:
                return result
        if not lowered:
            return None

        if "таймер" in lowered and (
            re.search(r"\b(постав|установ|запуст|созда)\w*", lowered)
            or re.match(r"^таймер\b", lowered)
        ):
            parsed_duration = self._parse_duration(lowered)
            if not parsed_duration:
                raise ValueError(
                    "Укажите длительность таймера, например «на 10 минут»."
                )
            seconds, duration_fragment = parsed_duration
            label = self._strip_command_parts(
                original,
                re.search(
                    r"(?:поставь|установи|запусти|создай)?\s*таймер",
                    original,
                    re.IGNORECASE,
                ).group(0),
                duration_fragment,
            )
            label = re.sub(r"^(?:(?:на|для)\s+)+", "", label, flags=re.IGNORECASE)
            item = self.create_timer(seconds, label or "Таймер")
            return {
                "intent": {"action": "create_timer", "item_id": item["id"]},
                "response": f"Таймер «{item['title']}» установлен на {duration_fragment}.",
                "item": item,
            }

        open_match = re.match(
            r"^(?:пожалуйста[,.]?\s*)?(?:открой|запусти|open|launch)\s+(.+)$",
            lowered,
        )
        if open_match:
            if not allow_app_launch:
                raise PermissionError(
                    "Запуск приложений доступен только с этого компьютера."
                )
            name = self.launcher.launch(open_match.group(1))
            return {
                "intent": {"action": "open_app", "app": open_match.group(1)},
                "response": f"Открываю «{name}».",
            }

        reminder_match = re.match(
            r"^(?:пожалуйста[,.]?\s*)?напомни(?:\s+мне)?\s+(.+)$",
            original,
            re.IGNORECASE,
        )
        if reminder_match:
            remainder = reminder_match.group(1)
            duration = self._parse_duration(remainder)
            due: datetime | None = None
            fragment = ""
            if duration and "через" in remainder.casefold():
                due = _utc_now() + timedelta(seconds=duration[0])
                fragment = duration[1]
            else:
                extracted = self._extract_due(remainder)
                if extracted:
                    due, fragment = extracted
            if due is None:
                raise ValueError(
                    "Укажите время: «через 20 минут» или «завтра в 09:00»."
                )
            title = self._strip_command_parts(remainder, fragment)
            title = re.sub(r"\bчерез\b", " ", title, count=1, flags=re.IGNORECASE)
            title = " ".join(title.split())
            if not title:
                title = "Напоминание"
            item = self.create_reminder(title, due.isoformat())
            return {
                "intent": {"action": "create_reminder", "item_id": item["id"]},
                "response": f"Хорошо, напомню: «{item['title']}».",
                "item": item,
            }

        if re.search(r"\b(добавь|создай|запиши)\w*\b", lowered) and re.search(
            r"\b(календар|событи|встреч)\w*\b", lowered
        ):
            extracted = self._extract_due(original)
            if not extracted:
                raise ValueError("Укажите дату и время события.")
            due, fragment = extracted
            title = re.sub(
                r"\b(?:добавь|создай|запиши)\w*\b|\b(?:в|на)\s+календар\w*\b|\bсобыти\w*\b",
                " ",
                original,
                flags=re.IGNORECASE,
            )
            title = self._strip_command_parts(title, fragment)
            item = self.store.create_item("event", title or "Событие", due_at=due)
            return {
                "intent": {"action": "create_event", "item_id": item["id"]},
                "response": f"Событие «{item['title']}» добавлено в календарь.",
                "item": item,
            }

        note_match = re.match(
            r"^(?:создай|добавь|запиши)?\s*(?:новую\s+)?заметк\w*\s*[:—-]?\s*(.+)$",
            original,
            re.IGNORECASE,
        )
        if note_match:
            item = self.create_note(note_match.group(1))
            return {
                "intent": {"action": "create_note", "item_id": item["id"]},
                "response": f"Заметка сохранена: «{item['title']}».",
                "item": item,
            }

        complete_match = re.match(
            r"^(?:заверши|выполни|отметь(?:\s+как\s+выполненн\w*)?)\s+"
            r"(?:запись|таймер|напоминание|событие|заметку)?\s*#?(\d+)$",
            lowered,
        )
        if complete_match:
            item_id = int(complete_match.group(1))
            self.store.complete_item(item_id)
            return {
                "intent": {"action": "complete_item", "item_id": item_id},
                "response": f"Запись #{item_id} отмечена как выполненная.",
            }

        delete_match = re.match(
            r"^(?:удали|отмени)\s+(?:запись|таймер|напоминание|событие|заметку)?\s*#?(\d+)$",
            lowered,
        )
        if delete_match:
            item_id = int(delete_match.group(1))
            self.store.delete_item(item_id)
            return {
                "intent": {"action": "delete_item", "item_id": item_id},
                "response": f"Запись #{item_id} удалена.",
            }

        list_patterns = {
            "timer": r"\b(?:покажи|какие|список)\b.*\bтаймер",
            "reminder": r"\b(?:покажи|какие|список)\b.*\bнапомин",
            "event": r"\b(?:покажи|что|какие)\b.*\b(?:календар|событи|план)",
            "note": r"\b(?:покажи|какие|список)\b.*\bзамет",
        }
        for kind, pattern in list_patterns.items():
            if re.search(pattern, lowered):
                items = self.store.list_items(kind=kind, limit=5)
                labels = {
                    "timer": "активных таймеров",
                    "reminder": "напоминаний",
                    "event": "событий",
                    "note": "заметок",
                }
                if not items:
                    response = f"Сейчас нет {labels[kind]}."
                else:
                    response = f"{labels[kind].capitalize()}: " + "; ".join(
                        f"#{item['id']} {item['title']}" for item in items
                    )
                return {
                    "intent": {"action": "list_items", "kind": kind},
                    "response": response,
                }

        greetings = (
            "привет",
            "здравствуй",
            "доброе утро",
            "добрый день",
            "добрый вечер",
        )
        if any(lowered.startswith(greeting) for greeting in greetings):
            return {
                "intent": {"action": "conversation"},
                "response": (
                    "Привет! Я готов помочь: могу поставить таймер, создать напоминание, "
                    "добавить событие, сохранить заметку или открыть приложение."
                ),
            }
        if re.search(r"\b(что ты умеешь|помощь|команды|help)\b", lowered):
            return {
                "intent": {"action": "help"},
                "response": (
                    "Я управляю таймерами, напоминаниями, календарём, заметками, "
                    "приложениями и GitHub. Скажите, например: «напомни через 20 минут "
                    "позвонить» или «открой калькулятор»."
                ),
            }
        if re.search(r"\b(который час|сколько времени|текущее время)\b", lowered):
            return {
                "intent": {"action": "current_time"},
                "response": f"Сейчас {datetime.now().astimezone():%H:%M}.",
            }
        return None

    def export_ics(self) -> str:
        def escape(value: str) -> str:
            return (
                value.replace("\r\n", "\n")
                .replace("\r", "\n")
                .replace("\\", "\\\\")
                .replace("\n", "\\n")
                .replace(",", "\\,")
                .replace(";", "\\;")
            )

        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Genie Assistant//RU",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
        ]
        for item in self.store.list_items(include_completed=True, limit=1000):
            if item["kind"] not in {"reminder", "event"} or not item["due_at"]:
                continue
            due = _parse_datetime(item["due_at"])
            created = _parse_datetime(item["created_at"])
            lines.extend(
                [
                    "BEGIN:VEVENT",
                    f"UID:genie-{item['id']}@local",
                    f"DTSTAMP:{created:%Y%m%dT%H%M%SZ}",
                    f"DTSTART:{due:%Y%m%dT%H%M%SZ}",
                    f"SUMMARY:{escape(item['title'])}",
                    f"DESCRIPTION:{escape(item['details'])}",
                    "END:VEVENT",
                ]
            )
        lines.append("END:VCALENDAR")
        return "\r\n".join(lines) + "\r\n"

    def close(self) -> None:
        self._stop_event.set()
        if self._scheduler and self._scheduler.is_alive():
            self._scheduler.join(timeout=2)

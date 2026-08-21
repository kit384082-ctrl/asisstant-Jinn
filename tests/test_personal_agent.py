from __future__ import annotations

import base64
import os
import sqlite3
import stat
import tempfile
import threading
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import Mock, patch

from personal_agent import AgendaStore, AppLauncher, DesktopNotifier, PersonalAgent

UTC = timezone.utc


class FakeNotifier(DesktopNotifier):
    def __init__(self) -> None:
        self.messages: list[tuple[str, str]] = []

    def send(self, title: str, message: str) -> bool:
        self.messages.append((title, message))
        return True


class PersonalAgentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.database = Path(self.tempdir.name) / "private" / "agent.db"
        self.notifier = FakeNotifier()
        self.agent = PersonalAgent(
            self.database,
            start_scheduler=False,
            notifier=self.notifier,
        )

    def tearDown(self) -> None:
        self.agent.close()
        self.tempdir.cleanup()

    def test_items_persist_and_can_be_completed_or_deleted(self):
        timer = self.agent.create_timer(60, "Чай")
        note = self.agent.create_note("Идея", "Проверить прототип")
        event = self.agent.create_event(
            "Созвон",
            (datetime.now(UTC) + timedelta(hours=2)).isoformat(),
        )

        reopened = AgendaStore(self.database)
        self.assertEqual(
            {item["kind"] for item in reopened.list_items()}, {"timer", "note", "event"}
        )
        reopened.complete_item(timer["id"])
        reopened.delete_item(note["id"])
        remaining = reopened.list_items()
        self.assertEqual([item["id"] for item in remaining], [event["id"]])

    @unittest.skipIf(
        os.name == "nt", "POSIX permission bits are not meaningful on Windows"
    )
    def test_data_file_has_private_permissions(self):
        self.assertEqual(stat.S_IMODE(self.database.parent.stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE(self.database.stat().st_mode), 0o600)

    @unittest.skipIf(
        os.name == "nt", "POSIX permission bits are not meaningful on Windows"
    )
    def test_existing_data_directory_permissions_are_not_changed(self):
        shared = Path(self.tempdir.name) / "existing"
        shared.mkdir(mode=0o755)
        database = shared / "second.db"
        store = AgendaStore(database)
        store.create_item("note", "Проверка разрешений")
        self.assertEqual(stat.S_IMODE(shared.stat().st_mode), 0o755)
        self.assertEqual(stat.S_IMODE(database.stat().st_mode), 0o600)

        auxiliary_files = (Path(f"{database}-wal"), Path(f"{database}-shm"))
        for path in auxiliary_files:
            path.touch(mode=0o644)
            path.chmod(0o644)
        store._restrict_data_files()
        for path in auxiliary_files:
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)

    def test_due_notifications_are_claimed_once(self):
        item = self.agent.store.create_item(
            "timer",
            "Перерыв",
            due_at=datetime.now(UTC) - timedelta(seconds=1),
        )
        first = self.agent.process_due_notifications()
        second = self.agent.process_due_notifications()

        self.assertEqual(len(first), 1)
        self.assertEqual(second, [])
        self.assertEqual(first[0]["item_id"], item["id"])
        self.assertEqual(self.notifier.messages, [("Таймер завершён", "Перерыв")])

    def test_concurrent_due_collection_does_not_duplicate(self):
        self.agent.store.create_item(
            "reminder",
            "Одно уведомление",
            due_at=datetime.now(UTC) - timedelta(seconds=1),
        )
        barrier = threading.Barrier(3)
        results: list[list[dict[str, object]]] = []

        def collect() -> None:
            barrier.wait()
            results.append(self.agent.store.collect_due())

        threads = [threading.Thread(target=collect) for _ in range(2)]
        for thread in threads:
            thread.start()
        barrier.wait()
        for thread in threads:
            thread.join(timeout=2)

        self.assertEqual(sum(len(result) for result in results), 1)
        self.assertEqual(len(self.agent.store.list_notifications()), 1)

    def test_russian_commands_create_list_complete_and_delete(self):
        timer = self.agent.try_execute("Поставь таймер на 2 минуты для чая")
        reminder = self.agent.try_execute("Напомни через 20 минут позвонить маме")
        note = self.agent.try_execute("Создай заметку: идея для проекта")

        self.assertEqual(timer["intent"]["action"], "create_timer")
        self.assertEqual(timer["item"]["title"], "чая")
        self.assertEqual(reminder["intent"]["action"], "create_reminder")
        self.assertEqual(note["intent"]["action"], "create_note")
        listed = self.agent.try_execute("Покажи список заметок")
        self.assertIn("идея для проекта", listed["response"])

        note_id = note["item"]["id"]
        completed = self.agent.try_execute(f"Отметь как выполненную запись #{note_id}")
        self.assertEqual(completed["intent"]["action"], "complete_item")
        timer_id = timer["item"]["id"]
        deleted = self.agent.try_execute(f"Удали таймер #{timer_id}")
        self.assertEqual(deleted["intent"]["action"], "delete_item")

    def test_localized_timer_commands_use_clean_default_titles(self):
        examples = {
            "en": ("Set a timer for 2 minutes", "Timer"),
            "de": ("Stelle einen Timer für 2 Minuten", "Timer"),
            "es": ("Pon un temporizador de 2 minutos", "Temporizador"),
            "fr": ("Lance un minuteur de 2 minutes", "Minuteur"),
        }
        for language, (command, expected_title) in examples.items():
            with self.subTest(language=language):
                result = self.agent.try_execute(command, language=language)
                self.assertEqual(result["intent"]["action"], "create_timer")
                self.assertEqual(result["item"]["title"], expected_title)

    def test_ambiguous_start_verbs_are_classified_as_timers(self):
        examples = {
            "ru": "Запусти таймер на 2 минуты",
            "en": "Start a timer for 2 minutes",
            "de": "Starte einen Timer für 2 Minuten",
            "es": "Inicia un temporizador de 2 minutos",
            "fr": "Lance un minuteur de 2 minutes",
        }
        for language, command in examples.items():
            with self.subTest(language=language):
                self.assertTrue(PersonalAgent.is_timer_command(command, language))
                result = self.agent.try_execute(command, language=language)
                self.assertEqual(result["intent"]["action"], "create_timer")

    def test_german_relative_reminder_keeps_relative_marker(self):
        result = self.agent.try_execute(
            "Erinnere mich in 20 Minuten anzurufen",
            language="de",
        )
        self.assertEqual(result["intent"]["action"], "create_reminder")
        self.assertIn("anzurufen", result["item"]["title"])

    def test_application_launch_can_be_disabled_for_remote_requests(self):
        for language, command in {
            "ru": "Открой зарегистрированное приложение",
            "en": "Open registered application",
            "de": "Öffne registrierte Anwendung",
            "es": "Abre aplicación registrada",
            "fr": "Ouvre application enregistrée",
        }.items():
            with self.subTest(language=language), self.assertRaises(PermissionError):
                self.agent.try_execute(
                    command, language=language, allow_app_launch=False
                )

    def test_native_notification_title_follows_selected_language(self):
        self.agent.set_language("fr-FR")
        self.agent.store.create_item(
            "timer",
            "Pause",
            due_at=datetime.now(UTC) - timedelta(seconds=1),
        )
        notification = self.agent.process_due_notifications()[0]
        self.assertEqual(notification["kind"], "timer")
        self.assertEqual(notification["title"], "Minuteur terminé")
        self.assertEqual(self.notifier.messages[-1], ("Minuteur terminé", "Pause"))

    def test_natural_reminders_reject_past_dates_and_unbounded_durations(self):
        yesterday = (datetime.now().astimezone() - timedelta(days=1)).date().isoformat()
        with self.assertRaisesRegex(ValueError, "в прошлом"):
            self.agent.try_execute(f"Напомни {yesterday} в 12:00 проверить почту")
        with self.assertRaisesRegex(ValueError, "слишком большая длительность"):
            self.agent.try_execute(f"Напомни через {'9' * 400} дней проверить почту")

    def test_ics_export_contains_events_and_escapes_text(self):
        due = datetime(2027, 1, 2, 10, 30, tzinfo=UTC)
        self.agent.create_event(
            "Встреча, команда", due.isoformat(), "Строка 1\r\nСтрока; 2"
        )
        self.agent.create_note("Не экспортировать")

        calendar = self.agent.export_ics()
        self.assertTrue(calendar.endswith("END:VCALENDAR\r\n"))
        self.assertIn("DTSTART:20270102T103000Z", calendar)
        self.assertIn(r"SUMMARY:Встреча\, команда", calendar)
        self.assertIn(r"DESCRIPTION:Строка 1\nСтрока\; 2", calendar)
        self.assertNotIn("Не экспортировать", calendar)

    def test_store_rejects_invalid_kind_and_missing_due_date(self):
        with self.assertRaises(ValueError):
            self.agent.store.create_item("unknown", "Запись")
        with self.assertRaises(ValueError):
            self.agent.store.create_item("reminder", "Запись")

    def test_database_schema_enforces_item_kinds(self):
        with (
            sqlite3.connect(self.database) as connection,
            self.assertRaises(sqlite3.IntegrityError),
        ):
            connection.execute(
                "INSERT INTO items(kind, title, created_at) VALUES (?, ?, ?)",
                ("command", "unsafe", datetime.now(UTC).isoformat()),
            )


class AppLauncherTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.store = AgendaStore(self.root / "agent.db")
        self.launcher = AppLauncher(self.store)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def make_executable(self, name: str = "safe-app") -> Path:
        executable = self.root / name
        executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        executable.chmod(0o700)
        return executable

    def test_custom_app_requires_absolute_executable_path(self):
        with self.assertRaisesRegex(ValueError, "абсолютный путь"):
            self.launcher.register("Небезопасно", "python")
        not_executable = self.root / "document.txt"
        not_executable.write_text("text", encoding="utf-8")
        if os.name == "posix":
            with self.assertRaisesRegex(ValueError, "исполняемым"):
                self.launcher.register("Документ", str(not_executable))

    def test_windows_custom_apps_require_native_executables(self):
        script = self.make_executable("unsafe.cmd")
        executable = self.make_executable("safe.exe")
        with patch("personal_agent.platform.system", return_value="Windows"):
            with self.assertRaisesRegex(ValueError, "исполняемым"):
                self.launcher.register("Сценарий", str(script))
            app = self.launcher.register("Windows программа", str(executable))
        self.assertTrue(app["available"])

    def test_application_environment_roots_must_be_absolute_and_nonempty(self):
        for value in ("", "   ", "relative/path"):
            with (
                self.subTest(value=value),
                patch("personal_agent.os.getenv", return_value=value),
            ):
                self.assertIsNone(AppLauncher._environment_root("APPDATA"))
        with patch("personal_agent.os.getenv", return_value=str(self.root)):
            self.assertEqual(AppLauncher._environment_root("APPDATA"), self.root)

    def test_custom_app_launch_uses_argument_array_without_shell(self):
        executable = self.make_executable()
        self.launcher.register("Моя программа Ёлка", str(executable))

        with patch("personal_agent.subprocess.Popen") as popen:
            launched = self.launcher.launch("Моя программа Елка")

        self.assertEqual(launched, "Моя программа Ёлка")
        args, kwargs = popen.call_args
        self.assertEqual(args[0], [str(executable.resolve())])
        self.assertNotIn("shell", kwargs)
        self.assertTrue(kwargs["close_fds"])

    def test_public_app_responses_do_not_expose_executable_paths(self):
        executable = self.make_executable()
        app = self.launcher.register("Секретный путь", str(executable))
        listed = next(
            item for item in self.launcher.list_apps() if item["alias"] == app["alias"]
        )
        self.assertNotIn("executable", app)
        self.assertNotIn("executable", listed)

    def test_builtin_aliases_cannot_be_shadowed_by_custom_apps(self):
        executable = self.make_executable()
        for name in ("Браузер", "VS Code", "Visual Studio Code"):
            with (
                self.subTest(name=name),
                self.assertRaisesRegex(ValueError, "зарезервировано"),
            ):
                self.launcher.register(name, str(executable))

    def test_custom_app_availability_rechecks_executable_permission(self):
        executable = self.make_executable()
        app = self.launcher.register("Временная программа", str(executable))
        if os.name == "posix":
            executable.chmod(0o600)
            listed = next(
                item
                for item in self.launcher.list_apps()
                if item["alias"] == app["alias"]
            )
            self.assertFalse(listed["available"])
            with self.assertRaisesRegex(ValueError, "исполняемому"):
                self.launcher.launch(app["alias"])

    def test_unknown_app_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "не найдено"):
            self.launcher.launch("несуществующее приложение")


class DesktopNotifierTests(unittest.TestCase):
    def test_windows_notification_passes_only_encoded_content(self):
        notifier = DesktopNotifier()
        dangerous = "'; Remove-Item -Recurse C:\\\\*; '"
        process = Mock()
        with (
            patch("personal_agent.platform.system", return_value="Windows"),
            patch(
                "personal_agent.shutil.which",
                return_value=r"C:\\Windows\\powershell.exe",
            ),
            patch("personal_agent.subprocess.Popen", process),
            patch(
                "personal_agent.subprocess.CREATE_NO_WINDOW", 0x08000000, create=True
            ),
        ):
            self.assertTrue(notifier.send("Джинн", dangerous))

        command = process.call_args.args[0]
        self.assertNotIn(dangerous, command)
        encoded_script = command[-1]
        script = base64.b64decode(encoded_script).decode("utf-16-le")
        self.assertNotIn(dangerous, script)
        self.assertIn(base64.b64encode(dangerous.encode()).decode(), script)
        self.assertNotIn("shell", process.call_args.kwargs)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from gui_server import create_server


class FakeController:
    def __init__(self):
        self.closed = False
        self.commands = []

    def status(self):
        return {
            "connected": False,
            "last_error": "",
            "settings": {"github_repo": "owner/repo", "branch": "main"},
            "dependencies": {"pygithub": False, "openai": False, "voice": False},
        }

    def connect(self, force=False):
        result = self.status()
        result["connected"] = True
        return result

    def disconnect(self):
        pass

    def execute_action(self, action, language="ru"):
        if action != "check_issues":
            raise ValueError("Неизвестное быстрое действие.")
        return {"intent": {"action": action}, "response": "Открытых задач нет."}

    def execute_text(self, text, language="ru", *, allow_local_apps=True):
        self.commands.append((text, language, allow_local_apps))
        return {"intent": {"action": "unknown"}, "response": text}

    def save_settings(self, payload):
        return self.status()

    def list_agenda(self, include_completed=False):
        return {"items": [], "agent": {"counts": {}}}

    def notifications(self, after_id):
        return {"notifications": [{"id": after_id + 1, "title": "Тест"}]}

    def list_apps(self):
        return {"apps": [{"alias": "browser", "name": "Браузер"}]}

    def create_timer(self, payload):
        return {"item": {"id": 1, "kind": "timer"}, "agent": {"counts": {}}}

    def export_calendar(self):
        return "BEGIN:VCALENDAR\r\nEND:VCALENDAR\r\n"

    def close(self):
        self.closed = True


class GuiServerTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        root = Path(self.tempdir.name)
        (root / "index.html").write_text(
            "<!doctype html><title>Genie</title>", encoding="utf-8"
        )
        self.controller = FakeController()
        self.server = create_server(
            "127.0.0.1", 0, controller=self.controller, web_root=root
        )
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.tempdir.cleanup()

    def get_json(self, path):
        with urlopen(self.base_url + path, timeout=2) as response:
            return response, json.loads(response.read())

    def post_json(self, path, value):
        request = Request(
            self.base_url + path,
            data=json.dumps(value).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=2) as response:
            return json.loads(response.read())

    def test_serves_index_with_security_headers(self):
        with urlopen(self.base_url + "/", timeout=2) as response:
            body = response.read().decode()
            self.assertIn("Genie", body)
            self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
            self.assertIn("default-src", response.headers["Content-Security-Policy"])

    def test_status_never_wraps_an_error(self):
        _, data = self.get_json("/api/status")
        self.assertTrue(data["ok"])
        self.assertEqual(data["settings"]["branch"], "main")

    def test_remote_status_hides_repository_and_local_metadata(self):
        request = Request(
            self.base_url + "/api/status",
            headers={"Host": "preview.example"},
        )
        with urlopen(request, timeout=2) as response:
            data = json.loads(response.read())
        self.assertEqual(data["settings"], {"branch": "main"})

    def test_post_rate_limit_is_bounded_per_client_group(self):
        for _ in range(30):
            self.assertTrue(self.server.allow_request("127.0.0.1", "/api/command"))
        self.assertFalse(self.server.allow_request("127.0.0.1", "/api/command"))
        self.assertTrue(self.server.allow_request("127.0.0.1", "/api/settings"))

    def test_action_endpoint(self):
        data = self.post_json("/api/action", {"action": "check_issues"})
        self.assertTrue(data["ok"])
        self.assertEqual(data["intent"]["action"], "check_issues")

    def test_unknown_action_returns_bad_request(self):
        with self.assertRaises(HTTPError) as raised:
            self.post_json("/api/action", {"action": "delete_repository"})
        self.assertEqual(raised.exception.code, 400)
        payload = json.loads(raised.exception.read())
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["code"], "BAD_REQUEST")
        self.assertTrue(payload["solution"])

    def test_non_json_content_type_returns_unsupported_media_type(self):
        request = Request(
            self.base_url + "/api/command",
            data=b"{}",
            headers={"Content-Type": "text/plain"},
            method="POST",
        )
        with self.assertRaises(HTTPError) as raised:
            urlopen(request, timeout=2)
        self.assertEqual(raised.exception.code, 415)

    def test_non_object_json_returns_bad_request(self):
        with self.assertRaises(HTTPError) as raised:
            self.post_json("/api/command", ["not", "an", "object"])
        self.assertEqual(raised.exception.code, 400)

    def test_non_string_command_returns_bad_request(self):
        with self.assertRaises(HTTPError) as raised:
            self.post_json("/api/command", {"text": 42})
        self.assertEqual(raised.exception.code, 400)

    def test_personal_agent_endpoints(self):
        _, agenda = self.get_json("/api/agenda")
        self.assertTrue(agenda["ok"])
        self.assertEqual(agenda["items"], [])

        timer = self.post_json("/api/timers", {"duration_seconds": 60})
        self.assertEqual(timer["item"]["kind"], "timer")

        _, notifications = self.get_json("/api/notifications?after=7")
        self.assertEqual(notifications["notifications"][0]["id"], 8)

        _, apps = self.get_json("/api/apps")
        self.assertEqual(apps["apps"][0]["alias"], "browser")

    def test_calendar_export_has_download_headers(self):
        with urlopen(self.base_url + "/api/calendar/export", timeout=2) as response:
            self.assertEqual(response.headers.get_content_type(), "text/calendar")
            self.assertIn("genie-calendar.ics", response.headers["Content-Disposition"])
            self.assertIn(b"BEGIN:VCALENDAR", response.read())

    def test_remote_proxy_host_cannot_change_settings_or_launch_apps(self):
        for path in ("/api/settings", "/api/apps/launch"):
            request = Request(
                self.base_url + path,
                data=b"{}",
                headers={"Content-Type": "application/json", "Host": "preview.example"},
                method="POST",
            )
            with self.assertRaises(HTTPError) as raised:
                urlopen(request, timeout=2)
            self.assertEqual(raised.exception.code, 403)

    def test_remote_command_blocks_every_localized_launch_alias(self):
        commands = (
            ("start calculator", "en"),
            ("oeffne terminal", "de"),
            ("lanza calculadora", "es"),
            ("démarre calculatrice", "fr"),
        )
        for text, language in commands:
            with self.subTest(text=text):
                request = Request(
                    self.base_url + "/api/command",
                    data=json.dumps({"text": text, "language": language}).encode(),
                    headers={
                        "Content-Type": "application/json",
                        "Host": "preview.example",
                    },
                    method="POST",
                )
                with self.assertRaises(HTTPError) as raised:
                    urlopen(request, timeout=2)
                self.assertEqual(raised.exception.code, 403)

    def test_remote_command_allows_ambiguous_french_timer_syntax(self):
        request = Request(
            self.base_url + "/api/command",
            data=json.dumps(
                {"text": "Lance un minuteur de 2 minutes", "language": "fr"}
            ).encode(),
            headers={"Content-Type": "application/json", "Host": "preview.example"},
            method="POST",
        )
        with urlopen(request, timeout=2) as response:
            payload = json.loads(response.read())
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["response"], "Lance un minuteur de 2 minutes")
        self.assertEqual(
            self.controller.commands[-1],
            ("Lance un minuteur de 2 minutes", "fr", False),
        )

    def test_unknown_api_route_returns_not_found(self):
        with self.assertRaises(HTTPError) as raised:
            self.get_json("/api/missing")
        self.assertEqual(raised.exception.code, 404)


if __name__ == "__main__":
    unittest.main()

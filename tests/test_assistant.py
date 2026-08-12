from __future__ import annotations

import unittest

from assistant import AssistantService, execute_intent


class FakeGitHub:
    def __init__(self):
        self.appended = None
        self.closed = False

    def get_notifications(self):
        return [{"title": "Review requested"}, {"title": "Build passed"}]

    def get_active_issues(self):
        return [{"number": 7, "title": "Fix login"}]

    def get_active_prs(self):
        return []

    def get_latest_action_status(self):
        return "Последний workflow «tests»: success."

    def get_recent_commits_summary(self):
        return "Последние коммиты: «Add GUI»."

    def append_to_file(self, path, content, message):
        self.appended = (path, content, message)
        return f"Текст добавлен в {path} в ветке main."

    def close(self):
        self.closed = True


class FakeParser:
    def parse_intent(self, text):
        return {"action": "check_issues"}


class ExecuteIntentTests(unittest.TestCase):
    def setUp(self):
        self.github = FakeGitHub()

    def test_notifications_response(self):
        response = execute_intent({"action": "check_notifications"}, self.github)
        self.assertIn("2 уведомления", response)
        self.assertIn("Review requested", response)

    def test_issues_response(self):
        response = execute_intent({"action": "check_issues"}, self.github)
        self.assertIn("#7", response)
        self.assertIn("Fix login", response)

    def test_empty_pull_requests(self):
        self.assertEqual(
            execute_intent({"action": "check_prs"}, self.github),
            "Открытых pull request’ов нет.",
        )

    def test_append_strips_content(self):
        response = execute_intent(
            {
                "action": "append_file",
                "file_path": "notes.md",
                "content": "  новая строка  ",
                "commit_message": "Add note",
            },
            self.github,
        )
        self.assertIn("notes.md", response)
        self.assertEqual(self.github.appended, ("notes.md", "новая строка", "Add note"))

    def test_append_rejects_empty_content(self):
        response = execute_intent(
            {"action": "append_file", "file_path": "notes.md", "content": "  "},
            self.github,
        )
        self.assertIn("Не удалось определить", response)
        self.assertIsNone(self.github.appended)

    def test_unknown_is_safe(self):
        response = execute_intent({"action": "delete_repository"}, self.github)
        self.assertIn("Не удалось распознать", response)

    def test_service_validates_and_closes(self):
        service = AssistantService(self.github, FakeParser())
        intent, response = service.execute_text("задачи")
        self.assertEqual(intent["action"], "check_issues")
        self.assertIn("Fix login", response)
        with self.assertRaises(ValueError):
            service.execute_text(" ")
        with self.assertRaises(ValueError):
            service.execute_action("delete_repository")
        service.close()
        self.assertTrue(self.github.closed)


if __name__ == "__main__":
    unittest.main()

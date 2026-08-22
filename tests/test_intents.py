from __future__ import annotations

import unittest
from types import SimpleNamespace

from github_service.intents import IntentParser


from typing import Any

class FakeCompletions:
    def __init__(self, content: str):
        self.content = content
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        message = SimpleNamespace(content=self.content)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class FakeOpenAI:
    def __init__(self, content: str):
        self.chat = SimpleNamespace(completions=FakeCompletions(content))


class IntentParserTests(unittest.TestCase):
    def test_local_read_actions(self):
        examples = {
            "Проверь мои уведомления": "check_notifications",
            "Покажи открытые задачи": "check_issues",
            "Какие pull request’ы открыты?": "check_prs",
            "Как прошла последняя сборка?": "check_actions",
            "Покажи последние коммиты": "recent_commits",
        }
        for command, expected in examples.items():
            with self.subTest(command=command):
                self.assertEqual(IntentParser.parse_local(command)["action"], expected)

    def test_append_with_path_before_content(self):
        intent = IntentParser.parse_local("Добавь в файл docs/notes.md купить молоко")
        self.assertEqual(intent["action"], "append_file")
        self.assertEqual(intent["file_path"], "docs/notes.md")
        self.assertEqual(intent["content"], "купить молоко")

    def test_append_with_path_after_content(self):
        intent = IntentParser.parse_local("добавь купить молоко в notes.md")
        self.assertEqual(intent["file_path"], "notes.md")
        self.assertEqual(intent["content"], "купить молоко")

    def test_append_defaults_to_notes(self):
        intent = IntentParser.parse_local("Запиши в файл важную мысль")
        self.assertEqual(intent["file_path"], "notes.md")
        self.assertEqual(intent["content"], "важную мысль")

    def test_local_rule_avoids_remote_call(self):
        client = FakeOpenAI('{"action":"unknown"}')
        parser = IntentParser(client=client)
        self.assertEqual(parser.parse_intent("покажи issues")["action"], "check_issues")
        self.assertEqual(client.chat.completions.calls, [])

    def test_remote_json_in_markdown_is_validated(self):
        client = FakeOpenAI('```json\n{"action":"check_prs"}\n```')
        parser = IntentParser(client=client)
        self.assertEqual(
            parser.parse_intent("что сейчас требует ревью?")["action"], "check_prs"
        )
        self.assertEqual(len(client.chat.completions.calls), 1)

    def test_remote_cannot_invent_action(self):
        parser = IntentParser(client=FakeOpenAI('{"action":"delete_repository"}'))
        self.assertEqual(parser.parse_intent("удали все")["action"], "unknown")

    def test_malformed_remote_response_fails_closed(self):
        parser = IntentParser(client=FakeOpenAI("not json"))
        self.assertEqual(parser.parse_intent("абракадабра")["action"], "unknown")


if __name__ == "__main__":
    unittest.main()

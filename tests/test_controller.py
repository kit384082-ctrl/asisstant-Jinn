from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from gui_server import AssistantController
from personal_agent import PersonalAgent


class FakeConversation:
    def __init__(self) -> None:
        self.messages: list[str] = []
        self.languages: list[str] = []
        self.local_app_permissions: list[bool] = []
        self.closed = False

    def reply(
        self, text: str, language: str = "ru", *, allow_local_apps: bool = False
    ) -> str:
        self.messages.append(text)
        self.languages.append(language)
        self.local_app_permissions.append(allow_local_apps)
        return f"Диалог: {text}"

    def clear(self) -> None:
        self.messages.clear()

    def close(self) -> None:
        self.closed = True


class AssistantControllerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.personal = PersonalAgent(
            Path(self.tempdir.name) / "agent.db",
            start_scheduler=False,
        )
        self.conversation = FakeConversation()
        self.controller = AssistantController(
            personal_agent=self.personal,
            conversation=self.conversation,  # type: ignore[arg-type]
        )

    def tearDown(self) -> None:
        self.controller.close()
        self.tempdir.cleanup()

    def test_personal_commands_are_routed_before_conversation(self):
        result = self.controller.execute_text("Поставь таймер на 1 минуту")
        self.assertEqual(result["intent"]["action"], "create_timer")
        self.assertEqual(self.conversation.messages, [])

    def test_unknown_text_uses_conversation_without_connecting_github(self):
        result = self.controller.execute_text("Расскажи короткую шутку")
        self.assertEqual(result["intent"]["action"], "conversation")
        self.assertEqual(result["response"], "Диалог: Расскажи короткую шутку")
        self.assertFalse(self.controller.status()["connected"])

    def test_status_contains_agent_state_but_no_secrets(self):
        status = self.controller.status()
        self.assertIn("agent", status)
        self.assertIn("counts", status["agent"])
        self.assertNotIn("github_token", status["settings"])
        self.assertNotIn("openai_api_key", status["settings"])

    def test_language_is_forwarded_to_conversation(self):
        self.controller.execute_text("Tell me a joke", language="en-US")
        self.assertEqual(self.conversation.languages, ["en"])

    def test_blank_secret_fields_preserve_existing_credentials(self):
        with patch("gui_server.Config.save") as save:
            self.controller.save_settings(
                {
                    "github_token": "",
                    "openai_api_key": "  ",
                    "google_api_key": "",
                    "anthropic_api_key": "",
                    "groq_api_key": "",
                    "custom_api_key": "",
                    "openai_model": "new-model",
                }
            )
        saved = save.call_args.args[0]
        self.assertEqual(saved, {"OPENAI_MODEL": "new-model"})

    def test_local_provider_settings_are_saved_without_a_secret(self):
        with patch("gui_server.Config.save") as save:
            self.controller.save_settings(
                {
                    "ai_provider": "local",
                    "ollama_model": "qwen2.5:1.5b",
                    "ollama_base_url": "http://127.0.0.1:11434/v1",
                }
            )
        self.assertEqual(
            save.call_args.args[0],
            {
                "AI_PROVIDER": "local",
                "OLLAMA_MODEL": "qwen2.5:1.5b",
                "OLLAMA_BASE_URL": "http://127.0.0.1:11434/v1",
            },
        )

    def test_local_provider_rejects_a_remote_endpoint(self):
        with self.assertRaisesRegex(ValueError, "локальным"):
            self.controller.save_settings(
                {
                    "ai_provider": "local",
                    "ollama_base_url": "https://ollama.example/v1",
                }
            )

    def test_close_stops_all_owned_services(self):
        self.controller.close()
        self.assertTrue(self.conversation.closed)
        self.assertIsNone(self.controller._service)


if __name__ == "__main__":
    unittest.main()

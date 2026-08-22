from __future__ import annotations

import json
import sys
import unittest
from types import SimpleNamespace
from typing import Any
from unittest.mock import Mock, patch

from conversation import ConversationService, _NoProviderRedirects
from errors import ActionableError

GENERATION_SETTINGS = {
    "timeout": 30.0,
    "temperature": 0.35,
    "top_p": 0.9,
    "max_tokens": 1200,
    "frequency_penalty": 0.0,
}
OPENAI_SETTINGS = {
    "provider": "openai",
    "key": "local-test-key",
    "base_url": "https://api.openai.com/v1",
    "model": "test-model",
    **GENERATION_SETTINGS,
}
LOCAL_SETTINGS = {
    "provider": "local",
    "key": "",
    "base_url": "http://127.0.0.1:11434/v1",
    "model": "jinn",
    **GENERATION_SETTINGS,
}


class ConversationServiceTests(unittest.TestCase):
    def test_local_fallback_does_not_require_provider_key(self):
        service = ConversationService()
        settings = {**OPENAI_SETTINGS, "key": ""}
        with patch.object(service, "_active_settings", return_value=settings):
            answer = service.reply("Как дела?")
        self.assertIn("ключ выбранного AI-провайдера", answer)
        self.assertIn("таймеры", answer)
        service.close()

    def test_missing_key_fallback_is_localized(self):
        service = ConversationService()
        settings = {**OPENAI_SETTINGS, "key": ""}
        with patch.object(service, "_active_settings", return_value=settings):
            answer = service.reply("How are you?", language="en-US")
        self.assertIn("selected AI provider", answer)
        self.assertIn("Local timers", answer)

    def test_local_ollama_profile_needs_no_api_key(self):
        service = ConversationService()
        completion = Mock()
        completion.chat.completions.create.return_value = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="Bonjour !"))]
        )
        with (
            patch.object(service, "_active_settings", return_value=LOCAL_SETTINGS),
            patch.object(service, "_get_client", return_value=completion),
        ):
            self.assertEqual(service.reply("Bonjour", language="fr"), "Bonjour !")
        request = completion.chat.completions.create.call_args.kwargs
        self.assertEqual(request["model"], "jinn")
        self.assertEqual(request["temperature"], 0.35)
        self.assertEqual(request["top_p"], 0.9)
        self.assertEqual(request["max_tokens"], 1200)
        self.assertEqual(request["frequency_penalty"], 0.0)
        self.assertIn("identity is Jinn", request["messages"][0]["content"])
        self.assertIn("français", request["messages"][0]["content"])

    def test_openai_compatible_client_uses_configured_timeout(self):
        service = ConversationService()
        client = Mock()
        constructor = Mock(return_value=client)
        fake_openai = SimpleNamespace(OpenAI=constructor)
        with patch.dict(sys.modules, {"openai": fake_openai}):
            self.assertIs(service._get_client(LOCAL_SETTINGS), client)
        constructor.assert_called_once_with(
            api_key="ollama-local",
            base_url="http://127.0.0.1:11434/v1",
            timeout=30.0,
            max_retries=1,
        )

    def test_local_model_tools_are_allowlisted_and_bounded(self):
        executed = []

        def execute(name, arguments, allow_local_apps):
            executed.append((name, arguments, allow_local_apps))
            return {"ok": True, "launched": "Calculator"}

        service = ConversationService(execute)
        completion = Mock()
        tool_call = SimpleNamespace(
            id="call-1",
            function=SimpleNamespace(
                name="launch_registered_app", arguments='{"alias":"calculator"}'
            ),
        )
        completion.chat.completions.create.side_effect = (
            SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(content="", tool_calls=[tool_call])
                    )
                ]
            ),
            SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content="Opened"))]
            ),
        )
        with (
            patch.object(service, "_active_settings", return_value=LOCAL_SETTINGS),
            patch.object(service, "_get_client", return_value=completion),
            patch("conversation.Config.WEB_SEARCH_ENABLED", True),
        ):
            self.assertEqual(
                service.reply("Open calculator", language="en", allow_local_apps=True),
                "Opened",
            )
        self.assertEqual(
            executed, [("launch_registered_app", {"alias": "calculator"}, True)]
        )
        first_request = completion.chat.completions.create.call_args_list[0].kwargs
        self.assertEqual(
            {tool["function"]["name"] for tool in first_request["tools"]},
            {"launch_registered_app", "search_internet"},
        )
        second_request = completion.chat.completions.create.call_args_list[1].kwargs
        self.assertEqual(second_request["tool_choice"], "none")

    def test_local_tool_failures_include_bounded_actionable_guidance(self):
        def reject_tool(_name, _arguments, _allow_local_apps):
            raise ActionableError(
                "FORBIDDEN_LOCAL_ONLY",
                "Launch denied",
                "Open Jinn through localhost.",
            )

        service = ConversationService(reject_tool)
        completion = Mock()
        tool_call = SimpleNamespace(
            id="call-denied",
            function=SimpleNamespace(
                name="launch_registered_app", arguments='{"alias":"calculator"}'
            ),
        )
        completion.chat.completions.create.side_effect = (
            SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(content="", tool_calls=[tool_call])
                    )
                ]
            ),
            SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content="Denied"))]
            ),
        )
        with (
            patch.object(service, "_active_settings", return_value=LOCAL_SETTINGS),
            patch.object(service, "_get_client", return_value=completion),
        ):
            self.assertEqual(
                service.reply("Open calculator", language="en", allow_local_apps=True),
                "Denied",
            )

        follow_up = completion.chat.completions.create.call_args_list[1].kwargs
        tool_message = next(
            message for message in follow_up["messages"] if message["role"] == "tool"
        )
        error = json.loads(tool_message["content"])
        self.assertEqual(error["code"], "FORBIDDEN_LOCAL_ONLY")
        self.assertEqual(error["error"], "Launch denied")
        self.assertEqual(error["solution"], "Open Jinn through localhost.")
        self.assertLessEqual(len(tool_message["content"]), 8000)

    def test_remote_local_model_request_never_receives_launch_tool(self):
        with patch("conversation.Config.WEB_SEARCH_ENABLED", True):
            tools = ConversationService._local_tool_specs(False)
        self.assertEqual(
            [tool["function"]["name"] for tool in tools], ["search_internet"]
        )

    def test_local_ollama_failure_has_actionable_localized_fallback(self):
        expected = {
            "ru": "Запустите Ollama",
            "en": "Start Ollama",
            "de": "Starte Ollama",
            "es": "Inicia Ollama",
            "fr": "Démarrez Ollama",
        }
        for locale, phrase in expected.items():
            service = ConversationService()
            with (
                self.subTest(locale=locale),
                patch.object(service, "_active_settings", return_value=LOCAL_SETTINGS),
                patch.object(
                    service,
                    "_openai_reply",
                    side_effect=ConnectionError("connection refused"),
                ),
                self.assertRaises(RuntimeError) as raised,
            ):
                service.reply("Hello", language=locale)
            self.assertIn("Jinn", str(raised.exception))
            self.assertIn(phrase, raised.exception.solution)
            self.assertIn("ollama create jinn", raised.exception.solution)

    def test_local_ollama_rejects_remote_endpoint(self):
        service = ConversationService()
        settings = {**LOCAL_SETTINGS, "base_url": "https://ollama.example/v1"}
        with (
            patch("conversation.Config.reload"),
            patch("conversation.Config.provider_settings", return_value=settings),
            self.assertRaises(ValueError),
        ):
            service._active_settings()

    def test_provider_reply_keeps_bounded_context(self) -> None:
        service = ConversationService()
        completion = Mock()
        completion.chat.completions.create.return_value = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="  Хорошо!  "))]
        )
        with (
            patch.object(service, "_active_settings", return_value=OPENAI_SETTINGS),
            patch.object(service, "_get_client", return_value=completion),
        ):
            for index in range(8):
                self.assertEqual(service.reply(f"Сообщение {index}"), "Хорошо!")

        self.assertEqual(len(service._history), 12)
        sent_messages = completion.chat.completions.create.call_args.kwargs["messages"]
        self.assertEqual(sent_messages[0]["role"], "system")
        self.assertEqual(sent_messages[-1]["role"], "user")

    def test_provider_or_language_change_does_not_share_history(self) -> None:
        service = ConversationService()
        settings = [
            OPENAI_SETTINGS,
            {
                "provider": "groq",
                "key": "different-key",
                "base_url": "https://api.groq.com/openai/v1",
                "model": "groq-model",
                **GENERATION_SETTINGS,
            },
        ]
        sent: list[list[dict[str, str]]] = []

        def reply(_settings: Any, messages: Any, *, allow_local_apps: bool = False) -> tuple[str, list[dict[str, str]]]:
            sent.append(messages)
            return "answer", []

        with (
            patch.object(service, "_active_settings", side_effect=settings),
            patch.object(service, "_openai_reply", side_effect=reply),
        ):
            service.reply("first", language="en")
            service.reply("zweite", language="de")

        self.assertEqual([message["content"] for message in sent[1][1:]], ["zweite"])
        self.assertIn("Deutsch", sent[1][0]["content"])

    def test_gemini_adapter_uses_header_not_query_string(self):
        service = ConversationService()
        settings = {
            "provider": "gemini",
            "key": "gemini-secret",
            "base_url": "https://generativelanguage.googleapis.com/v1beta",
            "model": "gemini-test",
            **GENERATION_SETTINGS,
        }
        response = {"candidates": [{"content": {"parts": [{"text": "Hola"}]}}]}
        with (
            patch.object(service, "_active_settings", return_value=settings),
            patch.object(service, "_post_json", return_value=response) as post,
        ):
            self.assertEqual(service.reply("Hola", language="es"), "Hola")
        url, headers, payload = post.call_args.args
        self.assertNotIn(settings["key"], url)
        self.assertEqual(headers["x-goog-api-key"], settings["key"])
        self.assertEqual(post.call_args.kwargs["timeout"], 30.0)
        self.assertEqual(
            payload["generationConfig"],
            {"temperature": 0.35, "topP": 0.9, "maxOutputTokens": 1200},
        )
        self.assertIn("español", payload["systemInstruction"]["parts"][0]["text"])

    def test_anthropic_adapter_uses_native_message_shape(self):
        service = ConversationService()
        settings = {
            "provider": "anthropic",
            "key": "anthropic-secret",
            "base_url": "https://api.anthropic.com/v1",
            "model": "claude-test",
            **GENERATION_SETTINGS,
        }
        response = {"content": [{"type": "text", "text": "Bonjour"}]}
        with (
            patch.object(service, "_active_settings", return_value=settings),
            patch.object(service, "_post_json", return_value=response) as post,
        ):
            self.assertEqual(service.reply("Bonjour", language="fr"), "Bonjour")
        url, headers, payload = post.call_args.args
        self.assertEqual(url, "https://api.anthropic.com/v1/messages")
        self.assertEqual(headers["x-api-key"], settings["key"])
        self.assertEqual(post.call_args.kwargs["timeout"], 30.0)
        self.assertEqual(payload["temperature"], 0.35)
        self.assertEqual(payload["top_p"], 0.9)
        self.assertEqual(payload["max_tokens"], 1200)
        self.assertEqual(payload["messages"][0]["role"], "user")
        self.assertIn("français", payload["system"])

    def test_provider_error_never_echoes_api_key(self):
        service = ConversationService()
        with (
            patch.object(service, "_active_settings", return_value=OPENAI_SETTINGS),
            patch.object(
                service,
                "_openai_reply",
                side_effect=RuntimeError(
                    f"request failed with {OPENAI_SETTINGS['key']}"
                ),
            ),
            self.assertRaises(RuntimeError) as raised,
        ):
            service.reply("Ответь")
        self.assertNotIn(OPENAI_SETTINGS["key"], str(raised.exception))
        self.assertIn("[redacted]", str(raised.exception))

    def test_native_provider_requests_reject_untrusted_hosts(self):
        with self.assertRaisesRegex(ValueError, "not allowed"):
            ConversationService._post_json(
                "https://attacker.example/collect",
                {"x-api-key": "local-secret"},
                {"message": "hello"},
                base_url="https://api.example/v1",
                timeout=5,
            )

    def test_native_provider_redirects_are_explicitly_rejected(self):
        handler = _NoProviderRedirects()
        self.assertIsNone(
            handler.redirect_request(
                Mock(), Mock(), 302, "Found", {}, "https://attacker.example/collect"
            )
        )

    def test_empty_provider_response_is_rejected(self):
        service = ConversationService()
        completion = Mock()
        completion.chat.completions.create.return_value = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=" "))]
        )
        with (
            patch.object(service, "_active_settings", return_value=OPENAI_SETTINGS),
            patch.object(service, "_get_client", return_value=completion),
            self.assertRaisesRegex(RuntimeError, "пустой ответ"),
        ):
            service.reply("Ответь")

    def test_close_closes_created_client_and_clears_history(self):
        service = ConversationService()
        client = Mock()
        service._client = client
        service._history.append({"role": "user", "content": "text"})
        service.close()
        client.close.assert_called_once_with()
        self.assertEqual(service._history, [])
        self.assertIsNone(service._history_configuration)


if __name__ == "__main__":
    unittest.main()

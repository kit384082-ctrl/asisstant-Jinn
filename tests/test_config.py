from __future__ import annotations

import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from config import BASE_DIR, Config


class ConfigTests(unittest.TestCase):
    def test_save_preserves_comments_and_unknown_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            env_file = Path(directory) / ".env"
            env_file.write_text(
                "# comment\nOTHER=value\nGITHUB_REPO=old/repo\nGITHUB_REPO=stale/repo\n",
                encoding="utf-8",
            )
            Config.save(
                {"GITHUB_REPO": "new/repo", "OPENAI_MODEL": "test-model"},
                env_path=env_file,
                reload_config=False,
            )
            content = env_file.read_text(encoding="utf-8")
            self.assertIn("# comment", content)
            self.assertIn("OTHER=value", content)
            self.assertIn('GITHUB_REPO="new/repo"', content)
            self.assertIn('OPENAI_MODEL="test-model"', content)
            if hasattr(stat, "S_IMODE"):
                self.assertEqual(stat.S_IMODE(env_file.stat().st_mode), 0o600)

    def test_save_escapes_values(self):
        with tempfile.TemporaryDirectory() as directory:
            env_file = Path(directory) / ".env"
            Config.save(
                {"OPENAI_MODEL": 'model "quoted"'},
                env_path=env_file,
                reload_config=False,
            )
            self.assertIn(r'OPENAI_MODEL="model \"quoted\""', env_file.read_text())

    def test_unknown_setting_is_rejected(self):
        with self.assertRaises(ValueError):
            Config.save({"DANGEROUS_UNKNOWN_KEY": "x"}, reload_config=False)

    def test_local_provider_endpoint_must_be_loopback(self):
        for allowed in (
            "http://127.0.0.1:11434/v1",
            "http://localhost:11434/v1",
            "http://[::1]:11434/v1",
        ):
            with self.subTest(allowed=allowed):
                Config.validate_local_base_url(allowed)
        for rejected in (
            "https://ollama.example/v1",
            "http://192.168.1.2:11434/v1",
            "http://user@127.0.0.1:11434/v1",
        ):
            with self.subTest(rejected=rejected), self.assertRaises(ValueError):
                Config.validate_local_base_url(rejected)

    def test_save_rejects_remote_local_provider_endpoint(self):
        with tempfile.TemporaryDirectory() as directory, self.assertRaises(ValueError):
            Config.save(
                {"OLLAMA_BASE_URL": "https://ollama.example/v1"},
                env_path=Path(directory) / ".env",
                reload_config=False,
            )

    def test_cloud_endpoints_require_safe_https_roots(self):
        Config.validate_provider_base_url("OPENAI_BASE_URL", "https://api.example/v1")
        Config.validate_provider_base_url("CUSTOM_BASE_URL", "http://localhost:8080/v1")
        rejected = (
            "http://api.example/v1",
            "https://user:pass@example.com/v1",
            "https://example.com/v1?token=secret",
            "https://127.0.0.1/v1",
            "https://192.168.1.4/v1",
        )
        for endpoint in rejected:
            with self.subTest(endpoint=endpoint), self.assertRaises(ValueError):
                Config.validate_provider_base_url("OPENAI_BASE_URL", endpoint)

    def test_numeric_and_boolean_settings_are_bounded(self):
        with tempfile.TemporaryDirectory() as directory:
            env_file = Path(directory) / ".env"
            Config.save(
                {
                    "AI_SMALL_MODEL_MODE": "true",
                    "AI_TEMPERATURE": "1.25",
                    "WEB_SEARCH_MAX_RESULTS": "8",
                },
                env_path=env_file,
                reload_config=False,
            )
            for key, value in (
                ("AI_TEMPERATURE", "2.1"),
                ("WEB_SEARCH_MAX_RESULTS", "9"),
                ("AI_SMALL_MODEL_MODE", "perhaps"),
            ):
                with self.subTest(key=key), self.assertRaises(ValueError):
                    Config.save({key: value}, env_path=env_file, reload_config=False)

    def test_public_settings_never_contain_tokens(self):
        secret_values = {
            "GITHUB_TOKEN": "ghp_test_secret_value",
            "OPENAI_API_KEY": "sk-test-secret-value",
            "GOOGLE_API_KEY": "google-test-secret-value",
            "ANTHROPIC_API_KEY": "anthropic-test-secret-value",
            "GROQ_API_KEY": "groq-test-secret-value",
            "CUSTOM_API_KEY": "custom-test-secret-value",
        }
        with patch.multiple(Config, **secret_values):
            settings = Config.public_settings()
        serialized = repr(settings)
        for value in secret_values.values():
            self.assertNotIn(value, serialized)
        forbidden = {
            "github_token",
            "openai_api_key",
            "google_api_key",
            "anthropic_api_key",
            "groq_api_key",
            "custom_api_key",
        }
        self.assertTrue(forbidden.isdisjoint(settings))
        self.assertIsInstance(settings["has_github_token"], bool)
        self.assertTrue(settings["providers"]["local"]["configured"])
        self.assertEqual(settings["providers"]["local"]["model"], Config.OLLAMA_MODEL)
        self.assertEqual(settings["ollama_base_url"], Config.OLLAMA_BASE_URL)
        for metadata in settings["providers"].values():
            self.assertEqual(
                set(metadata),
                {"configured", "model", "small_model", "active_model", "base_url"},
            )
            self.assertIsInstance(metadata["configured"], bool)
            self.assertNotIn("key", metadata)

    def test_each_provider_has_an_isolated_profile(self):
        values = {
            "OPENAI_API_KEY": "openai-key",
            "GOOGLE_API_KEY": "gemini-key",
            "ANTHROPIC_API_KEY": "anthropic-key",
            "GROQ_API_KEY": "groq-key",
            "OLLAMA_BASE_URL": "http://127.0.0.1:11434/v1",
            "OLLAMA_MODEL": "qwen2.5:1.5b",
            "CUSTOM_API_KEY": "custom-key",
            "CUSTOM_BASE_URL": "https://custom.example/v1",
            "CUSTOM_MODEL": "custom-model",
            "AI_SMALL_MODEL_MODE": False,
        }
        with patch.multiple(Config, **values):
            profiles = {
                provider: Config.provider_settings(provider)
                for provider in Config.SUPPORTED_PROVIDERS
            }
        self.assertEqual(
            {
                profiles[name]["key"]
                for name in ("openai", "gemini", "anthropic", "groq", "custom")
            },
            {"openai-key", "gemini-key", "anthropic-key", "groq-key", "custom-key"},
        )
        self.assertEqual(profiles["local"]["key"], "")
        self.assertEqual(profiles["local"]["model"], "qwen2.5:1.5b")
        self.assertEqual(profiles["local"]["base_url"], "http://127.0.0.1:11434/v1")
        self.assertEqual(profiles["custom"]["base_url"], "https://custom.example/v1")
        self.assertEqual(profiles["custom"]["model"], "custom-model")

    def test_default_wake_phrases_cover_every_supported_language(self):
        with patch.object(Config, "WAKE_WORDS", ""):
            for language in Config.SUPPORTED_LANGUAGES:
                with self.subTest(language=language):
                    self.assertTrue(Config.wake_words(language))

    def test_relative_agent_data_path_is_resolved_from_project_root(self):
        try:
            with (
                patch("config._load_env_file"),
                patch.dict("os.environ", {"AGENT_DATA_PATH": ".data/agent.db"}),
            ):
                Config.reload()
                self.assertEqual(
                    Config.AGENT_DATA_PATH,
                    str((BASE_DIR / ".data" / "agent.db").resolve()),
                )
        finally:
            Config.reload()


if __name__ == "__main__":
    unittest.main()

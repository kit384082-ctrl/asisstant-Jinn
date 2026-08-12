"""Application configuration loaded from environment variables and ``.env``."""

from __future__ import annotations

import ipaddress
import os
import re
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any, ClassVar
from urllib.parse import urlsplit

BASE_DIR = Path(__file__).resolve().parent


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        quote = value[0]
        value = value[1:-1]
        if quote == '"':
            value = (
                value.replace(r"\n", "\n")
                .replace(r"\r", "\r")
                .replace(r"\t", "\t")
                .replace(r"\"", '"')
                .replace(r"\\", "\\")
            )
    return value


def _load_env_file(path: Path, *, override: bool = False) -> None:
    """Load the small dotenv subset used by Genie without a hard dependency."""

    try:
        from dotenv import load_dotenv

        load_dotenv(path, override=override)
        return
    except ImportError:
        pass

    if not path.is_file():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
            continue
        if override or key not in os.environ:
            os.environ[key] = _unquote(value)


def _quote_env(value: object) -> str:
    text = str(value)
    escaped = (
        text.replace("\\", r"\\")
        .replace('"', r"\"")
        .replace("\n", r"\n")
        .replace("\r", r"\r")
    )
    return f'"{escaped}"'


def _is_loopback_url(value: str) -> bool:
    """Return whether an HTTP(S) endpoint is confined to this computer."""

    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        return False
    if port == 0:
        return False
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        return False
    if parsed.hostname.casefold() == "localhost":
        return True
    try:
        return ipaddress.ip_address(parsed.hostname).is_loopback
    except ValueError:
        return False


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().casefold() in {"1", "true", "yes", "on"}


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


class Config:
    """Reloadable configuration with a strict allowlist for UI-managed values."""

    ENV_FILE = Path(os.getenv("GENIE_ENV_FILE", str(BASE_DIR / ".env")))
    SUPPORTED_PROVIDERS: ClassVar[tuple[str, ...]] = (
        "openai",
        "gemini",
        "anthropic",
        "groq",
        "local",
        "custom",
    )
    SUPPORTED_LANGUAGES: ClassVar[tuple[str, ...]] = ("ru", "en", "de", "es", "fr")
    DEFAULT_TTS_VOICES: ClassVar[dict[str, str]] = {
        "ru": "ru-RU-SvetlanaNeural",
        "en": "en-US-JennyNeural",
        "de": "de-DE-KatjaNeural",
        "es": "es-ES-ElviraNeural",
        "fr": "fr-FR-DeniseNeural",
    }
    DEFAULT_WAKE_WORDS: ClassVar[dict[str, tuple[str, ...]]] = {
        "ru": ("джинн", "эй джинн", "джини"),
        "en": ("genie", "hey genie"),
        "de": ("dschinni", "hallo dschinni"),
        "es": ("genio", "hola genio"),
        "fr": ("génie", "salut génie"),
    }

    GITHUB_TOKEN = ""
    GITHUB_REPO = ""
    AI_PROVIDER = "openai"
    OPENAI_API_KEY = ""
    OPENAI_BASE_URL = "https://api.openai.com/v1"
    OPENAI_MODEL = "gpt-4o-mini"
    OPENAI_SMALL_MODEL = "gpt-4o-mini"
    GOOGLE_API_KEY = ""
    GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
    GEMINI_MODEL = "gemini-2.0-flash"
    GEMINI_SMALL_MODEL = "gemini-2.0-flash-lite"
    ANTHROPIC_API_KEY = ""
    ANTHROPIC_BASE_URL = "https://api.anthropic.com/v1"
    ANTHROPIC_MODEL = "claude-3-5-haiku-latest"
    ANTHROPIC_SMALL_MODEL = "claude-3-5-haiku-latest"
    GROQ_API_KEY = ""
    GROQ_BASE_URL = "https://api.groq.com/openai/v1"
    GROQ_MODEL = "llama-3.3-70b-versatile"
    GROQ_SMALL_MODEL = "llama-3.1-8b-instant"
    OLLAMA_BASE_URL = "http://127.0.0.1:11434/v1"
    OLLAMA_MODEL = "jinn"
    OLLAMA_SMALL_MODEL = "jinn"
    CUSTOM_API_KEY = ""
    CUSTOM_BASE_URL = ""
    CUSTOM_MODEL = ""
    CUSTOM_SMALL_MODEL = ""
    AI_SMALL_MODEL_MODE = False
    AI_REQUEST_TIMEOUT = 30.0
    AI_TEMPERATURE = 0.35
    AI_TOP_P = 0.9
    AI_MAX_TOKENS = 1200
    AI_FREQUENCY_PENALTY = 0.0
    WEB_SEARCH_ENABLED = False
    WEB_SEARCH_MAX_RESULTS = 5
    UI_LANGUAGE = "auto"
    VOICE_LANGUAGE = "ru-RU"
    WAKE_WORDS = ""
    VOSK_MODEL_PATH = "model"
    TTS_VOICE = "ru-RU-SvetlanaNeural"
    GUI_HOST = "127.0.0.1"
    GUI_PORT = 8765
    AGENT_DATA_PATH = str(BASE_DIR / ".genie" / "agent.db")
    GITHUB_BRANCH = "main"

    EDITABLE_KEYS: ClassVar[frozenset[str]] = frozenset(
        {
            "GITHUB_TOKEN",
            "GITHUB_REPO",
            "AI_PROVIDER",
            "OPENAI_API_KEY",
            "OPENAI_BASE_URL",
            "OPENAI_MODEL",
            "OPENAI_SMALL_MODEL",
            "GOOGLE_API_KEY",
            "GEMINI_BASE_URL",
            "GEMINI_MODEL",
            "GEMINI_SMALL_MODEL",
            "ANTHROPIC_API_KEY",
            "ANTHROPIC_BASE_URL",
            "ANTHROPIC_MODEL",
            "ANTHROPIC_SMALL_MODEL",
            "GROQ_API_KEY",
            "GROQ_BASE_URL",
            "GROQ_MODEL",
            "GROQ_SMALL_MODEL",
            "OLLAMA_BASE_URL",
            "OLLAMA_MODEL",
            "OLLAMA_SMALL_MODEL",
            "CUSTOM_API_KEY",
            "CUSTOM_BASE_URL",
            "CUSTOM_MODEL",
            "CUSTOM_SMALL_MODEL",
            "AI_SMALL_MODEL_MODE",
            "AI_REQUEST_TIMEOUT",
            "AI_TEMPERATURE",
            "AI_TOP_P",
            "AI_MAX_TOKENS",
            "AI_FREQUENCY_PENALTY",
            "WEB_SEARCH_ENABLED",
            "WEB_SEARCH_MAX_RESULTS",
            "UI_LANGUAGE",
            "VOICE_LANGUAGE",
            "WAKE_WORDS",
            "VOSK_MODEL_PATH",
            "TTS_VOICE",
            "GUI_HOST",
            "GUI_PORT",
            "AGENT_DATA_PATH",
        }
    )

    @classmethod
    def reload(cls, *, override: bool = False) -> None:
        _load_env_file(cls.ENV_FILE, override=override)
        cls.GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()
        cls.GITHUB_REPO = os.getenv("GITHUB_REPO", "").strip()
        provider = os.getenv("AI_PROVIDER", "openai").strip().casefold()
        cls.AI_PROVIDER = provider if provider in cls.SUPPORTED_PROVIDERS else "openai"
        cls.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
        cls.OPENAI_BASE_URL = (
            os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").strip()
            or "https://api.openai.com/v1"
        )
        cls.OPENAI_MODEL = (
            os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"
        )
        cls.OPENAI_SMALL_MODEL = (
            os.getenv("OPENAI_SMALL_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"
        )
        cls.GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "").strip()
        cls.GEMINI_BASE_URL = (
            os.getenv(
                "GEMINI_BASE_URL",
                "https://generativelanguage.googleapis.com/v1beta",
            ).strip()
            or "https://generativelanguage.googleapis.com/v1beta"
        )
        cls.GEMINI_MODEL = (
            os.getenv("GEMINI_MODEL", "gemini-2.0-flash").strip() or "gemini-2.0-flash"
        )
        cls.GEMINI_SMALL_MODEL = (
            os.getenv("GEMINI_SMALL_MODEL", "gemini-2.0-flash-lite").strip()
            or "gemini-2.0-flash-lite"
        )
        cls.ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
        cls.ANTHROPIC_BASE_URL = (
            os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com/v1").strip()
            or "https://api.anthropic.com/v1"
        )
        cls.ANTHROPIC_MODEL = (
            os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-latest").strip()
            or "claude-3-5-haiku-latest"
        )
        cls.ANTHROPIC_SMALL_MODEL = (
            os.getenv("ANTHROPIC_SMALL_MODEL", "claude-3-5-haiku-latest").strip()
            or "claude-3-5-haiku-latest"
        )
        cls.GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
        cls.GROQ_BASE_URL = (
            os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1").strip()
            or "https://api.groq.com/openai/v1"
        )
        cls.GROQ_MODEL = (
            os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()
            or "llama-3.3-70b-versatile"
        )
        cls.GROQ_SMALL_MODEL = (
            os.getenv("GROQ_SMALL_MODEL", "llama-3.1-8b-instant").strip()
            or "llama-3.1-8b-instant"
        )
        cls.OLLAMA_BASE_URL = (
            os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1").strip()
            or "http://127.0.0.1:11434/v1"
        )
        cls.OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "jinn").strip() or "jinn"
        cls.OLLAMA_SMALL_MODEL = (
            os.getenv("OLLAMA_SMALL_MODEL", "jinn").strip() or "jinn"
        )
        cls.CUSTOM_API_KEY = os.getenv("CUSTOM_API_KEY", "").strip()
        cls.CUSTOM_BASE_URL = os.getenv("CUSTOM_BASE_URL", "").strip()
        cls.CUSTOM_MODEL = os.getenv("CUSTOM_MODEL", "").strip()
        cls.CUSTOM_SMALL_MODEL = os.getenv("CUSTOM_SMALL_MODEL", "").strip()
        cls.AI_SMALL_MODEL_MODE = _env_bool("AI_SMALL_MODEL_MODE")
        cls.AI_REQUEST_TIMEOUT = _env_float("AI_REQUEST_TIMEOUT", 30.0)
        cls.AI_TEMPERATURE = _env_float("AI_TEMPERATURE", 0.35)
        cls.AI_TOP_P = _env_float("AI_TOP_P", 0.9)
        cls.AI_MAX_TOKENS = _env_int("AI_MAX_TOKENS", 1200)
        cls.AI_FREQUENCY_PENALTY = _env_float("AI_FREQUENCY_PENALTY", 0.0)
        cls.WEB_SEARCH_ENABLED = _env_bool("WEB_SEARCH_ENABLED")
        cls.WEB_SEARCH_MAX_RESULTS = _env_int("WEB_SEARCH_MAX_RESULTS", 5)
        ui_language = os.getenv("UI_LANGUAGE", "auto").strip().casefold()
        cls.UI_LANGUAGE = (
            ui_language if ui_language in {"auto", *cls.SUPPORTED_LANGUAGES} else "auto"
        )
        voice_language = os.getenv("VOICE_LANGUAGE", "ru-RU").strip() or "ru-RU"
        voice_code = voice_language.split("-", 1)[0].casefold()
        cls.VOICE_LANGUAGE = (
            voice_language if voice_code in cls.SUPPORTED_LANGUAGES else "ru-RU"
        )
        cls.WAKE_WORDS = os.getenv("WAKE_WORDS", "").strip()
        cls.VOSK_MODEL_PATH = os.getenv("VOSK_MODEL_PATH", "model").strip() or "model"
        cls.TTS_VOICE = os.getenv(
            "TTS_VOICE",
            cls.DEFAULT_TTS_VOICES.get(voice_code, cls.DEFAULT_TTS_VOICES["ru"]),
        ).strip() or cls.DEFAULT_TTS_VOICES.get(
            voice_code, cls.DEFAULT_TTS_VOICES["ru"]
        )
        cls.GUI_HOST = os.getenv("GUI_HOST", "127.0.0.1").strip() or "127.0.0.1"
        agent_data_value = os.getenv(
            "AGENT_DATA_PATH", str(BASE_DIR / ".genie" / "agent.db")
        ).strip() or str(BASE_DIR / ".genie" / "agent.db")
        agent_data_path = Path(agent_data_value).expanduser()
        if not agent_data_path.is_absolute():
            agent_data_path = BASE_DIR / agent_data_path
        cls.AGENT_DATA_PATH = str(agent_data_path.resolve())
        try:
            cls.GUI_PORT = int(os.getenv("GUI_PORT", "8765"))
        except ValueError:
            cls.GUI_PORT = 8765

    @classmethod
    def provider_settings(cls, provider: str | None = None) -> dict[str, Any]:
        """Return one provider's private runtime settings to backend code."""

        selected = (provider or cls.AI_PROVIDER).casefold()
        definitions = {
            "openai": {
                "key": cls.OPENAI_API_KEY,
                "base_url": cls.OPENAI_BASE_URL,
                "primary_model": cls.OPENAI_MODEL,
                "small_model": cls.OPENAI_SMALL_MODEL,
            },
            "gemini": {
                "key": cls.GOOGLE_API_KEY,
                "base_url": cls.GEMINI_BASE_URL,
                "primary_model": cls.GEMINI_MODEL,
                "small_model": cls.GEMINI_SMALL_MODEL,
            },
            "anthropic": {
                "key": cls.ANTHROPIC_API_KEY,
                "base_url": cls.ANTHROPIC_BASE_URL,
                "primary_model": cls.ANTHROPIC_MODEL,
                "small_model": cls.ANTHROPIC_SMALL_MODEL,
            },
            "groq": {
                "key": cls.GROQ_API_KEY,
                "base_url": cls.GROQ_BASE_URL,
                "primary_model": cls.GROQ_MODEL,
                "small_model": cls.GROQ_SMALL_MODEL,
            },
            "local": {
                "key": "",
                "base_url": cls.OLLAMA_BASE_URL,
                "primary_model": cls.OLLAMA_MODEL,
                "small_model": cls.OLLAMA_SMALL_MODEL,
            },
            "custom": {
                "key": cls.CUSTOM_API_KEY,
                "base_url": cls.CUSTOM_BASE_URL,
                "primary_model": cls.CUSTOM_MODEL,
                "small_model": cls.CUSTOM_SMALL_MODEL,
            },
        }
        if selected not in definitions:
            raise ValueError(f"Unsupported AI provider: {selected}")
        result = definitions[selected]
        model = (
            result["small_model"]
            if cls.AI_SMALL_MODEL_MODE and result["small_model"]
            else result["primary_model"]
        )
        return {
            "provider": selected,
            **result,
            "model": model,
            "small_model_mode": cls.AI_SMALL_MODEL_MODE,
            "timeout": cls.AI_REQUEST_TIMEOUT,
            "temperature": cls.AI_TEMPERATURE,
            "top_p": cls.AI_TOP_P,
            "max_tokens": cls.AI_MAX_TOKENS,
            "frequency_penalty": cls.AI_FREQUENCY_PENALTY,
        }

    @classmethod
    def wake_words(cls, language: str | None = None) -> tuple[str, ...]:
        custom = tuple(
            word.strip() for word in cls.WAKE_WORDS.split(",") if word.strip()
        )
        if custom:
            return custom
        code = (language or cls.VOICE_LANGUAGE).split("-", 1)[0].casefold()
        return cls.DEFAULT_WAKE_WORDS.get(code, cls.DEFAULT_WAKE_WORDS["ru"])

    @staticmethod
    def validate_local_base_url(value: str) -> None:
        """Reject Ollama endpoints that could send prompts off-device."""

        if not _is_loopback_url(value):
            raise ValueError(
                "OLLAMA_BASE_URL должен быть локальным HTTP(S)-адресом "
                "(127.0.0.1, ::1 или localhost)."
            )

    @classmethod
    def validate_provider_base_url(cls, name: str, value: str) -> None:
        """Validate an API root without accepting credentials or unsafe schemes."""

        if not isinstance(value, str) or not value.strip() or len(value) > 2048:
            raise ValueError(f"{name} должен быть непустым URL короче 2049 символов.")
        try:
            parsed = urlsplit(value.strip())
            port = parsed.port
        except ValueError as exc:
            raise ValueError(f"{name} содержит некорректный URL.") from exc
        if port == 0:
            raise ValueError(f"{name} содержит некорректный порт.")
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError(
                f"{name} должен быть HTTP(S)-адресом без учётных данных, "
                "параметров и фрагмента."
            )
        if name == "OLLAMA_BASE_URL":
            cls.validate_local_base_url(value)
            return
        if name == "CUSTOM_BASE_URL" and _is_loopback_url(value):
            return
        if parsed.scheme != "https":
            raise ValueError(f"{name} должен использовать HTTPS.")
        host = parsed.hostname.casefold().rstrip(".")
        if host == "localhost" or host.endswith((".localhost", ".local", ".internal")):
            raise ValueError(f"{name} не должен указывать во внутреннюю сеть.")
        try:
            address = ipaddress.ip_address(host)
        except ValueError:
            return
        if not address.is_global:
            raise ValueError(f"{name} не должен указывать на частный IP-адрес.")

    @classmethod
    def validate(
        cls,
        *,
        require_github: bool = True,
        require_openai: bool = False,
        require_voice: bool = False,
    ) -> None:
        """Validate only components needed by the selected run mode."""

        missing: list[str] = []
        if require_github:
            if not cls.GITHUB_TOKEN:
                missing.append("GITHUB_TOKEN")
            if not cls.GITHUB_REPO:
                missing.append("GITHUB_REPO")
        if (
            require_openai
            and cls.AI_PROVIDER != "local"
            and not cls.provider_settings()["key"]
        ):
            missing.append(f"{cls.AI_PROVIDER.upper()} API key")
        if require_voice and not cls.VOSK_MODEL_PATH:
            missing.append("VOSK_MODEL_PATH")
        if missing:
            raise ValueError(
                "Не заполнены обязательные настройки: " + ", ".join(missing)
            )

        if cls.GITHUB_REPO and not re.fullmatch(r"[^/\s]+/[^/\s]+", cls.GITHUB_REPO):
            raise ValueError("GITHUB_REPO должен иметь формат owner/repository.")
        for name, url in (
            ("OPENAI_BASE_URL", cls.OPENAI_BASE_URL),
            ("GEMINI_BASE_URL", cls.GEMINI_BASE_URL),
            ("ANTHROPIC_BASE_URL", cls.ANTHROPIC_BASE_URL),
            ("GROQ_BASE_URL", cls.GROQ_BASE_URL),
            ("OLLAMA_BASE_URL", cls.OLLAMA_BASE_URL),
            ("CUSTOM_BASE_URL", cls.CUSTOM_BASE_URL),
        ):
            if url:
                cls.validate_provider_base_url(name, url)
        if not 1 <= cls.AI_REQUEST_TIMEOUT <= 300:
            raise ValueError("AI_REQUEST_TIMEOUT должен быть от 1 до 300 секунд.")
        if not 0 <= cls.AI_TEMPERATURE <= 2:
            raise ValueError("AI_TEMPERATURE должна быть от 0 до 2.")
        if not 0 < cls.AI_TOP_P <= 1:
            raise ValueError("AI_TOP_P должен быть больше 0 и не больше 1.")
        if not 1 <= cls.AI_MAX_TOKENS <= 32768:
            raise ValueError("AI_MAX_TOKENS должен быть от 1 до 32768.")
        if not -2 <= cls.AI_FREQUENCY_PENALTY <= 2:
            raise ValueError("AI_FREQUENCY_PENALTY должен быть от -2 до 2.")
        if not 1 <= cls.WEB_SEARCH_MAX_RESULTS <= 8:
            raise ValueError("WEB_SEARCH_MAX_RESULTS должен быть от 1 до 8.")
        if not 0 <= cls.GUI_PORT <= 65535:
            raise ValueError("GUI_PORT должен быть в диапазоне от 0 до 65535.")
        if require_voice and not Path(cls.VOSK_MODEL_PATH).expanduser().is_dir():
            raise ValueError(
                f"Модель Vosk не найдена: {cls.VOSK_MODEL_PATH}. "
                "Укажите правильный VOSK_MODEL_PATH."
            )

    @classmethod
    def save(
        cls,
        values: Mapping[str, object],
        *,
        env_path: Path | str | None = None,
        reload_config: bool = True,
    ) -> None:
        """Safely update known keys in a dotenv file, preserving comments."""

        unknown = set(values) - cls.EDITABLE_KEYS
        if unknown:
            raise ValueError(f"Неизвестные настройки: {', '.join(sorted(unknown))}")
        for key, value in values.items():
            text = str(value)
            if len(text) > 4096 or any(
                character in text for character in ("\0", "\r", "\n")
            ):
                raise ValueError(
                    f"{key} содержит недопустимое или слишком длинное значение."
                )
        for key in (
            "OPENAI_BASE_URL",
            "GEMINI_BASE_URL",
            "ANTHROPIC_BASE_URL",
            "GROQ_BASE_URL",
            "OLLAMA_BASE_URL",
            "CUSTOM_BASE_URL",
        ):
            if key in values and str(values[key]).strip():
                cls.validate_provider_base_url(key, str(values[key]).strip())
        if (
            "AI_PROVIDER" in values
            and str(values["AI_PROVIDER"]).casefold() not in cls.SUPPORTED_PROVIDERS
        ):
            raise ValueError("Неизвестный AI-провайдер.")
        for key in ("AI_SMALL_MODEL_MODE", "WEB_SEARCH_ENABLED"):
            if key in values and str(values[key]).casefold() not in {
                "0",
                "1",
                "false",
                "true",
                "no",
                "yes",
                "off",
                "on",
            }:
                raise ValueError(f"{key} должен быть логическим значением.")
        numeric_ranges = {
            "AI_REQUEST_TIMEOUT": (1.0, 300.0),
            "AI_TEMPERATURE": (0.0, 2.0),
            "AI_TOP_P": (0.000001, 1.0),
            "AI_MAX_TOKENS": (1.0, 32768.0),
            "AI_FREQUENCY_PENALTY": (-2.0, 2.0),
            "WEB_SEARCH_MAX_RESULTS": (1.0, 8.0),
        }
        for key, (minimum, maximum) in numeric_ranges.items():
            if key not in values:
                continue
            try:
                number = float(str(values[key]))
            except ValueError as exc:
                raise ValueError(f"{key} должен быть числом.") from exc
            if not minimum <= number <= maximum:
                raise ValueError(f"{key} вне разрешённого диапазона.")
            if (
                key in {"AI_MAX_TOKENS", "WEB_SEARCH_MAX_RESULTS"}
                and not number.is_integer()
            ):
                raise ValueError(f"{key} должен быть целым числом.")

        path = Path(env_path) if env_path is not None else cls.ENV_FILE
        path.parent.mkdir(parents=True, exist_ok=True)
        lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
        pending = {key: str(value) for key, value in values.items()}
        requested_keys = set(pending)
        output: list[str] = []

        assignment = re.compile(r"^(\s*)(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=")
        for line in lines:
            match = assignment.match(line)
            key = match.group(2) if match else None
            if key in pending:
                output.append(f"{key}={_quote_env(pending.pop(key))}")
            elif key in requested_keys:
                continue
            else:
                output.append(line)

        if pending and output and output[-1].strip():
            output.append("")
        output.extend(f"{key}={_quote_env(value)}" for key, value in pending.items())
        content = "\n".join(output).rstrip() + "\n"

        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{path.name}.", dir=path.parent
        )
        temporary_path = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            temporary_path.chmod(0o600)
            os.replace(temporary_path, path)
        finally:
            temporary_path.unlink(missing_ok=True)

        if reload_config and path.resolve() == cls.ENV_FILE.resolve():
            for key, value in values.items():
                os.environ[key] = str(value)
            cls.reload()

    @classmethod
    def public_settings(cls) -> dict[str, object]:
        """Return browser-safe settings without returning any credential value."""

        providers = {
            name: {
                "configured": name == "local"
                or bool(cls.provider_settings(name)["key"]),
                "model": cls.provider_settings(name)["primary_model"],
                "small_model": cls.provider_settings(name)["small_model"],
                "active_model": cls.provider_settings(name)["model"],
                "base_url": cls.provider_settings(name)["base_url"],
            }
            for name in cls.SUPPORTED_PROVIDERS
        }
        return {
            "github_repo": cls.GITHUB_REPO,
            "has_github_token": bool(cls.GITHUB_TOKEN),
            "has_openai_key": bool(cls.OPENAI_API_KEY),
            "ai_provider": cls.AI_PROVIDER,
            "ai_small_model_mode": cls.AI_SMALL_MODEL_MODE,
            "ai_request_timeout": cls.AI_REQUEST_TIMEOUT,
            "ai_temperature": cls.AI_TEMPERATURE,
            "ai_top_p": cls.AI_TOP_P,
            "ai_max_tokens": cls.AI_MAX_TOKENS,
            "ai_frequency_penalty": cls.AI_FREQUENCY_PENALTY,
            "web_search_enabled": cls.WEB_SEARCH_ENABLED,
            "web_search_max_results": cls.WEB_SEARCH_MAX_RESULTS,
            "providers": providers,
            "openai_base_url": cls.OPENAI_BASE_URL,
            "gemini_base_url": cls.GEMINI_BASE_URL,
            "anthropic_base_url": cls.ANTHROPIC_BASE_URL,
            "groq_base_url": cls.GROQ_BASE_URL,
            "ollama_base_url": cls.OLLAMA_BASE_URL,
            "custom_base_url": cls.CUSTOM_BASE_URL,
            "ui_language": cls.UI_LANGUAGE,
            "voice_language": cls.VOICE_LANGUAGE,
            "wake_words": ", ".join(cls.wake_words()),
            "vosk_model_path": cls.VOSK_MODEL_PATH,
            "tts_voice": cls.TTS_VOICE,
            "branch": cls.GITHUB_BRANCH,
        }


Config.reload()

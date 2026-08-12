"""Speech-to-text and text-to-speech helpers with lazy audio initialization."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import tempfile
import threading
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class TTS:
    """Edge TTS with a lazy pyttsx3 fallback.

    No audio modules or devices are initialized during import, so the web GUI
    can run on headless machines and systems without a sound card.
    """

    def __init__(
        self,
        voice: str = "ru-RU-SvetlanaNeural",
        language: str | None = None,
    ):
        self.edge_voice = voice
        self.language = (language or voice).split("-", 1)[0].casefold()
        self._engine: Any | None = None
        self._lock = threading.Lock()

    def _get_offline_engine(self) -> Any:
        if self._engine is None:
            import pyttsx3

            self._engine = pyttsx3.init()
            voices = self._engine.getProperty("voices") or []
            markers = {
                "ru": ("russian", "ru-", "ru_", "рус"),
                "en": ("english", "en-", "en_"),
                "de": ("german", "deutsch", "de-", "de_"),
                "es": ("spanish", "español", "espanol", "es-", "es_"),
                "fr": ("french", "français", "francais", "fr-", "fr_"),
            }.get(self.language, (self.language,))
            for voice in voices:
                raw_languages = " ".join(
                    str(value) for value in (getattr(voice, "languages", None) or [])
                )
                identity = (
                    f"{getattr(voice, 'name', '')} {getattr(voice, 'id', '')} "
                    f"{raw_languages}"
                ).casefold()
                if any(marker in identity for marker in markers):
                    self._engine.setProperty("voice", voice.id)
                    break
        return self._engine

    async def _speak_edge(self, text: str) -> None:
        import edge_tts
        import pygame

        temp_filename: str | None = None
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            fd, temp_filename = tempfile.mkstemp(prefix="genie_tts_", suffix=".mp3")
            os.close(fd)
            await edge_tts.Communicate(text, self.edge_voice).save(temp_filename)
            pygame.mixer.music.load(temp_filename)
            pygame.mixer.music.play()
            clock = pygame.time.Clock()
            while pygame.mixer.music.get_busy():
                clock.tick(20)
            if hasattr(pygame.mixer.music, "unload"):
                pygame.mixer.music.unload()
        finally:
            if temp_filename:
                try:
                    Path(temp_filename).unlink(missing_ok=True)
                except OSError:
                    logger.debug(
                        "Could not delete temporary speech file", exc_info=True
                    )

    @staticmethod
    def _run_coroutine(coroutine: Any) -> None:
        """Run an async synthesizer even if the caller already owns an event loop."""

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(coroutine)
            return

        error: list[Exception] = []

        def runner() -> None:
            try:
                asyncio.run(coroutine)
            except Exception as exc:  # noqa: BLE001 - re-raised in caller
                error.append(exc)

        thread = threading.Thread(target=runner, name="genie-tts-event-loop")
        thread.start()
        thread.join()
        if error:
            raise error[0]

    def speak_pyttsx3(self, text: str) -> None:
        engine = self._get_offline_engine()
        engine.say(text)
        engine.runAndWait()

    def speak(self, text: str) -> bool:
        """Speak text and return whether any speech backend succeeded."""

        if not text or not text.strip():
            return False
        logger.info("Genie says: %s", text)
        with self._lock:
            try:
                self._run_coroutine(self._speak_edge(text))
                return True
            except Exception as edge_error:  # noqa: BLE001 - fallback boundary
                logger.warning("Edge TTS failed: %s; using pyttsx3", edge_error)
                try:
                    self.speak_pyttsx3(text)
                    return True
                except Exception as offline_error:  # noqa: BLE001 - audio driver boundary
                    logger.error("All TTS backends failed: %s", offline_error)
                    return False

    def close(self) -> None:
        if self._engine is not None:
            try:
                self._engine.stop()
            except Exception:
                logger.debug("Could not stop pyttsx3", exc_info=True)


class STT:
    def __init__(self, model_path: str, sample_rate: int = 16000):
        try:
            import vosk
        except ImportError as exc:
            raise RuntimeError(
                "Vosk не установлен. Выполните: pip install -r requirements.txt"
            ) from exc

        path = Path(model_path).expanduser()
        if not path.is_dir():
            raise ValueError(
                f"Модель Vosk не найдена: {model_path}. Укажите VOSK_MODEL_PATH в .env."
            )
        vosk.SetLogLevel(-1)
        self.model = vosk.Model(str(path))
        self.sample_rate = sample_rate
        self.recognizer = vosk.KaldiRecognizer(self.model, sample_rate)

    @staticmethod
    def _read_text(raw_json: str, key: str = "text") -> str:
        try:
            value = json.loads(raw_json).get(key, "")
        except (json.JSONDecodeError, AttributeError):
            logger.warning("Vosk returned invalid JSON")
            return ""
        return value.strip() if isinstance(value, str) else ""

    def reset(self) -> None:
        self.recognizer.Reset()

    def process_audio(self, data: bytes) -> str | None:
        """Return text when Vosk marks a phrase as complete."""

        if self.recognizer.AcceptWaveform(data):
            return self._read_text(self.recognizer.Result()) or None
        return None

    def partial_text(self) -> str:
        return self._read_text(self.recognizer.PartialResult(), key="partial")

    def final_text(self) -> str:
        return self._read_text(self.recognizer.FinalResult())

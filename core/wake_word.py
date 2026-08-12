"""Microphone wake-word and command capture."""

from __future__ import annotations

import logging
import queue
import threading
import time
import unicodedata
from collections.abc import Iterable
from typing import Any

from .stt_tts import STT

logger = logging.getLogger(__name__)


class WakeWordDetector:
    def __init__(
        self,
        model_path: str,
        wake_word: str | Iterable[str] = "джинн",
        *,
        sample_rate: int = 16000,
    ):
        try:
            import sounddevice
        except ImportError as exc:
            raise RuntimeError(
                "sounddevice не установлен. Выполните: pip install -r requirements.txt"
            ) from exc

        self.sd = sounddevice
        words = (wake_word,) if isinstance(wake_word, str) else tuple(wake_word)
        self.wake_words = tuple(
            self._normalize(word)
            for word in words
            if isinstance(word, str) and word.strip()
        )
        if not self.wake_words:
            raise ValueError("At least one wake phrase is required")
        # Keep the original singular attribute for third-party integrations.
        self.wake_word = self.wake_words[0]
        self.sample_rate = sample_rate
        self.stt = STT(model_path, sample_rate=sample_rate)
        self.q: queue.Queue[bytes] = queue.Queue(maxsize=32)
        self.block_size = sample_rate // 2

    @staticmethod
    def _normalize(value: str) -> str:
        normalized = unicodedata.normalize("NFKC", value).casefold().replace("ё", "е")
        # Speech engines may insert punctuation around or inside a phrase. Keep
        # Unicode letters/numbers and turn every separator into one safe space.
        words = "".join(
            character if unicodedata.category(character)[0] in {"L", "N"} else " "
            for character in normalized
        )
        return " ".join(words.split())

    @classmethod
    def _contains_wake_phrase(cls, heard: str, phrases: Iterable[str]) -> bool:
        normalized_heard = cls._normalize(heard)
        padded_heard = f" {normalized_heard} "
        return any(
            f" {normalized_phrase} " in padded_heard
            for phrase in phrases
            if (normalized_phrase := cls._normalize(phrase))
        )

    def audio_callback(
        self, indata: Any, frames: int, callback_time: Any, status: Any
    ) -> None:
        """Push audio from the sounddevice callback without blocking it."""

        if status:
            logger.warning("Microphone status: %s", status)
        try:
            self.q.put_nowait(bytes(indata))
        except queue.Full:
            # Drop the oldest chunk rather than blocking the real-time callback.
            try:
                self.q.get_nowait()
            except queue.Empty:
                pass
            try:
                self.q.put_nowait(bytes(indata))
            except queue.Full:
                pass

    def _clear_queue(self) -> None:
        while True:
            try:
                self.q.get_nowait()
            except queue.Empty:
                return

    def _stream(self) -> Any:
        return self.sd.RawInputStream(
            samplerate=self.sample_rate,
            blocksize=self.block_size,
            device=None,
            dtype="int16",
            channels=1,
            callback=self.audio_callback,
        )

    def listen_for_wake_word(self, stop_event: threading.Event | None = None) -> bool:
        """Listen until the wake word is found or cancellation is requested."""

        stop_event = stop_event or threading.Event()
        self._clear_queue()
        self.stt.reset()
        logger.info("Listening for wake phrases: %s", ", ".join(self.wake_words))
        with self._stream():
            while not stop_event.is_set():
                try:
                    data = self.q.get(timeout=0.25)
                except queue.Empty:
                    continue
                complete = self.stt.process_audio(data) or ""
                partial = self.stt.partial_text()
                heard = f"{complete} {partial}"
                if self._contains_wake_phrase(heard, self.wake_words):
                    logger.info("Wake word detected")
                    return True
        return False

    def listen_for_command(
        self,
        timeout_seconds: float = 10,
        stop_event: threading.Event | None = None,
    ) -> str:
        """Capture one command and retain the final partial phrase on timeout."""

        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        stop_event = stop_event or threading.Event()
        self._clear_queue()
        self.stt.reset()
        logger.info("Listening for command")
        deadline = time.monotonic() + timeout_seconds

        with self._stream():
            while not stop_event.is_set():
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    final = self.stt.final_text()
                    if final:
                        logger.info("Recognized final command: %s", final)
                    else:
                        logger.warning("Command listening timed out")
                    return final
                try:
                    data = self.q.get(timeout=min(0.25, remaining))
                except queue.Empty:
                    continue
                text = self.stt.process_audio(data)
                if text:
                    logger.info("Recognized command: %s", text)
                    return text
        return ""

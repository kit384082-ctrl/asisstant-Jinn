import sounddevice as sd
import queue
import sys
import logging
from .stt_tts import STT

logger = logging.getLogger(__name__)

class WakeWordDetector:
    def __init__(self, model_path: str, wake_word: str = "джинн"):
        self.wake_word = wake_word.lower()
        self.stt = STT(model_path)
        self.q = queue.Queue()
        self.sample_rate = 16000
        self.block_size = 8000 # 0.5 seconds

    def audio_callback(self, indata, frames, time, status):
        """This is called (from a separate thread) for each audio block."""
        if status:
            print(status, file=sys.stderr)
        self.q.put(bytes(indata))

    def listen_for_wake_word(self):
        """Blocks and listens until the wake word is detected."""
        logger.info(f"Listening for wake word: '{self.wake_word}'...")
        with sd.RawInputStream(samplerate=self.sample_rate, blocksize=self.block_size, device=None,
                               dtype='int16', channels=1, callback=self.audio_callback):
            while True:
                data = self.q.get()
                text = self.stt.process_audio(data)
                if text:
                    # Check if wake word is in the transcribed text
                    if self.wake_word in text.lower():
                        logger.info("Wake word detected!")
                        return True

    def listen_for_command(self, timeout_seconds=10) -> str:
        """Listens for a command after the wake word.
        Note: Vosk doesn't easily do 'timeout' natively with `AcceptWaveform` in a stream without
        managing time manually. We'll use a simple time limit."""
        import time
        logger.info("Listening for command...")

        start_time = time.time()

        # Clear queue before listening for command
        with self.q.mutex:
            self.q.queue.clear()

        with sd.RawInputStream(samplerate=self.sample_rate, blocksize=self.block_size, device=None,
                               dtype='int16', channels=1, callback=self.audio_callback):
            while True:
                if time.time() - start_time > timeout_seconds:
                    logger.warning("Command listening timed out.")
                    return ""

                try:
                    # Non-blocking get with timeout to allow checking overall timeout
                    data = self.q.get(timeout=1.0)
                    text = self.stt.process_audio(data)
                    if text:
                        logger.info(f"Recognized command: {text}")
                        return text
                except queue.Empty:
                    continue

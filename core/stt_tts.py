import pyttsx3
import asyncio
import edge_tts
import json
import logging
import tempfile
import os
import pygame
from typing import Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize pygame mixer for audio playback
pygame.mixer.init()

class TTS:
    def __init__(self):
        # Initialize offline fallback (pyttsx3)
        self.engine = pyttsx3.init()
        # Ensure English voice is selected for fallback
        voices = self.engine.getProperty('voices')
        for voice in voices:
            if 'english' in voice.name.lower() or 'en' in voice.id.lower():
                self.engine.setProperty('voice', voice.id)
                break

        # Edge TTS default voice
        self.edge_voice = "en-US-AriaNeural"

    async def speak_edge(self, text: str):
        """Attempts to speak using edge-tts (requires internet)"""
        temp_filename = None
        try:
            communicate = edge_tts.Communicate(text, self.edge_voice)

            # Using tempfile safely across platforms
            temp_dir = tempfile.gettempdir()
            temp_filename = os.path.join(temp_dir, f"genie_tts_{os.urandom(4).hex()}.mp3")

            await communicate.save(temp_filename)

            # Play using pygame
            pygame.mixer.music.load(temp_filename)
            pygame.mixer.music.play()

            # Block until playback is finished
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)

            pygame.mixer.music.unload()

        except Exception as e:
            logger.warning(f"Edge-TTS failed: {e}. Falling back to pyttsx3.")
            self.speak_pyttsx3(text)
        finally:
            if temp_filename and os.path.exists(temp_filename):
                try:
                    os.remove(temp_filename)
                except Exception as e:
                    logger.debug(f"Failed to remove temp audio file: {e}")

    def speak_pyttsx3(self, text: str):
        """Fallback offline text-to-speech"""
        self.engine.say(text)
        self.engine.runAndWait()

    def speak(self, text: str):
        """Main method to call for speaking."""
        logger.info(f"Genie says: {text}")
        try:
            # Use asyncio.run for robust event loop handling in Python 3.7+
            asyncio.run(self.speak_edge(text))
        except Exception as e:
            logger.error(f"Error running async edge-tts: {e}")
            self.speak_pyttsx3(text)

class STT:
    def __init__(self, model_path: str):
        import vosk
        if not __import__("os").path.exists(model_path):
            raise ValueError(f"Vosk model not found at {model_path}. Please download it and configure VOSK_MODEL_PATH in .env")

        vosk.SetLogLevel(-1) # Disable verbose logs
        self.model = vosk.Model(model_path)
        # Using 16000 sample rate as default for vosk
        self.recognizer = vosk.KaldiRecognizer(self.model, 16000)

    def process_audio(self, data: bytes) -> Optional[str]:
        """Process an audio chunk. Returns transcribed text if a full phrase is detected."""
        if self.recognizer.AcceptWaveform(data):
            result_json = self.recognizer.Result()
            result_dict = json.loads(result_json)
            text = result_dict.get('text', '')
            if text:
                return text
        return None

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    GITHUB_REPO = os.getenv("GITHUB_REPO")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    VOSK_MODEL_PATH = os.getenv("VOSK_MODEL_PATH", "model")

    @classmethod
    def validate(cls):
        missing = []
        if not cls.GITHUB_TOKEN:
            missing.append("GITHUB_TOKEN")
        if not cls.GITHUB_REPO:
            missing.append("GITHUB_REPO")
        if not cls.OPENAI_API_KEY:
            missing.append("OPENAI_API_KEY")
        if not cls.VOSK_MODEL_PATH:
            missing.append("VOSK_MODEL_PATH")

        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

# Genie: GitHub Voice Assistant

Genie is a Python-based voice assistant designed to help you interact with your GitHub repository using voice commands. It listens for the wake word "Джинн" (Genie in Russian), accepts Russian voice commands, performs actions directly on your configured GitHub repository's `main` branch, and responds in English.

## Features

- **Wake Word Detection:** Uses Vosk for lightweight, offline detection of the wake word "Джинн".
- **Russian Speech-to-Text (STT):** Converts your Russian voice commands into text using Vosk.
- **Intent Parsing:** Uses OpenAI's LLM to intelligently parse your commands into actionable GitHub intents.
- **GitHub Integration:**
  - Check unread notifications.
  - Check active issues and pull requests.
  - Check the status of recent GitHub Actions workflow runs.
  - Get a summary of recent commits.
  - **Append text to files directly on the `main` branch.**
- **English Text-to-Speech (TTS):** Uses `edge-tts` for natural-sounding English responses, with an offline fallback to `pyttsx3`.

## Prerequisites

1. **Python 3.8+**
2. **System Dependencies:**
   - On Linux, you may need `portaudio19-dev` and `python3-pyaudio python3-pygame` for the `sounddevice` library.
     `sudo apt-get install portaudio19-dev`
   - On Windows, `sounddevice` usually works out of the box.
   - For `edge-tts` playback, a system audio player using `pygame`. `pygame` is included in requirements.txt.
3. **Vosk Model:**
   - Download a small Russian Vosk model from [Vosk Models](https://alphacephei.com/vosk/models).
   - Recommended: `vosk-model-small-ru-0.22.zip`
   - Extract the zip file and place the extracted folder in the project directory, renaming it to `model` (or configure the path in `.env`).

## Setup Instructions

1. **Clone the repository:**
   `git clone <your-repository-url>`
   `cd <repository-directory>`

2. **Install dependencies:**
   `pip install -r requirements.txt`

3. **Configure Environment Variables:**
   - Copy the `.env.example` file to `.env`:
     `cp .env.example .env`
   - Edit `.env` and fill in your credentials:
     - `GITHUB_TOKEN`: Your GitHub Personal Access Token (PAT). Ensure it has `repo` permissions to read and write to the repository.
     - `GITHUB_REPO`: The target repository in the format `owner/repo` (e.g., `octocat/Hello-World`).
     - `OPENAI_API_KEY`: Your OpenAI API Key for intent parsing.
     - `VOSK_MODEL_PATH`: Path to the extracted Vosk model (default is `model`).

## Running the Assistant

Run the main script:

`python main.py`

1. Wait for the initialization (loading the model and connecting to GitHub).
2. Once you hear "Genie is online and ready," the assistant is listening in the background.
3. Say "Джинн" to wake it up.
4. Wait for it to reply "Yes, master?".
5. Speak your command in Russian. For example:
   - "Проверь мои уведомления" (Check my notifications)
   - "Добавь в файл notes.md купить молоко" (Add 'buy milk' to notes.md file)
   - "Какие последние коммиты?" (What are the recent commits?)
6. Genie will execute the action on the `main` branch and speak the result back to you in English.

## Architecture

- `main.py`: Entry point and main event loop.
- `core/wake_word.py`: Microphone listening and wake word detection using Vosk.
- `core/stt_tts.py`: Speech recognition (Vosk) and speech synthesis (edge-tts / pyttsx3).
- `github_service/client.py`: GitHub API client using PyGithub. Enforces operations on `main`.
- `github_service/intents.py`: Uses OpenAI to parse transcribed Russian text into JSON commands.
- `config.py`: Configuration loader and validator.

## Limitations & Notes
- The assistant is hardcoded to only operate on the `main` branch to prevent accidental branch creation or switching, as per the requirements.
- The `sounddevice` library requires exclusive access to your microphone.
- Natural sounding TTS requires an active internet connection for `edge-tts`.

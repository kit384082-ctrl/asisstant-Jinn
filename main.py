"""Genie entry point: web GUI by default, legacy voice loop on request."""

from __future__ import annotations

import argparse
import logging
import sys
import threading
import webbrowser

from config import Config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


def run_gui(host: str, port: int, *, open_browser: bool = True) -> int:
    from gui_server import create_server

    try:
        server = create_server(host, port)
    except OSError as exc:
        logger.error("Не удалось запустить GUI на %s:%s: %s", host, port, exc)
        return 1

    actual_host, actual_port = server.server_address[:2]
    # This compares an already-bound address; it does not open a listener.
    browser_host = (
        "127.0.0.1"
        if actual_host in {"0.0.0.0", "::"}  # noqa: S104 - comparison only.
        else actual_host
    )
    browser_host_str = browser_host.decode() if isinstance(browser_host, bytes) else str(browser_host)
    url = f"http://{browser_host_str}:{actual_port}"
    logger.info("Веб-интерфейс Джинна доступен по адресу %s", url)
    logger.info("Для остановки нажмите Ctrl+C")
    if open_browser:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        logger.info("Останавливаю Джинна…")
    finally:
        server.shutdown()
        server.server_close()
    return 0


def run_voice_only() -> int:
    """Run the original always-listening microphone mode without the GUI."""

    Config.reload()
    try:
        Config.validate(require_github=False, require_voice=True)
    except ValueError as exc:
        logger.error("Ошибка настроек: %s", exc)
        return 2

    service = None
    tts = None
    try:
        from core.stt_tts import TTS
        from core.wake_word import WakeWordDetector
        from gui_server import AssistantController

        service = AssistantController()
        detector = WakeWordDetector(Config.VOSK_MODEL_PATH, Config.wake_words())
        tts = TTS(Config.TTS_VOICE, language=Config.VOICE_LANGUAGE)
    except Exception as exc:  # noqa: BLE001 - startup dependency boundary
        if service is not None:
            service.close()
        if tts is not None:
            tts.close()
        logger.error("Не удалось запустить голосовой режим: %s", exc)
        return 1

    if service is None or tts is None:  # Defensive guard for static/runtime safety.
        logger.error("Не удалось инициализировать голосовые сервисы.")
        return 1
    locale = Config.VOICE_LANGUAGE.split("-", 1)[0].casefold()
    voice_copy = {
        "ru": ("Джинн запущен и готов к работе.", "Слушаю.", "Команда не распознана"),
        "en": (
            "Genie is running and ready.",
            "I’m listening.",
            "I could not recognize the command",
        ),
        "de": (
            "Dschinni ist gestartet und bereit.",
            "Ich höre zu.",
            "Der Befehl wurde nicht erkannt",
        ),
        "es": (
            "Genio está activo y listo.",
            "Te escucho.",
            "No se reconoció el comando",
        ),
        "fr": (
            "Génie est actif et prêt.",
            "Je vous écoute.",
            "La commande n’a pas été reconnue",
        ),
    }.get(
        locale, ("Джинн запущен и готов к работе.", "Слушаю.", "Команда не распознана")
    )
    stop_event = threading.Event()
    tts.speak(voice_copy[0])
    try:
        while not stop_event.is_set():
            if not detector.listen_for_wake_word(stop_event):
                break
            tts.speak(voice_copy[1])
            command = detector.listen_for_command(10, stop_event)
            if not command:
                logger.info("%s", voice_copy[2])
                continue
            logger.info("Распознано: %s", command)
            result = service.execute_text(command, language=locale)
            tts.speak(result["response"])
    except KeyboardInterrupt:
        logger.info("Останавливаю голосовой режим…")
        stop_event.set()
    except Exception:
        logger.exception("Ошибка в голосовом цикле")
        return 1
    finally:
        service.close()
        tts.close()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Джинн — голосовой GitHub-ассистент")
    parser.add_argument(
        "--voice-only",
        action="store_true",
        help="запустить фоновый режим Vosk без веб-интерфейса",
    )
    parser.add_argument("--host", default=Config.GUI_HOST, help="адрес GUI-сервера")
    parser.add_argument(
        "--port", default=Config.GUI_PORT, type=int, help="порт GUI-сервера"
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="не открывать браузер автоматически",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.voice_only:
        return run_voice_only()
    if not 0 <= args.port <= 65535:
        logger.error("Порт должен быть в диапазоне 0–65535")
        return 2
    return run_gui(args.host, args.port, open_browser=not args.no_browser)


if __name__ == "__main__":
    sys.exit(main())

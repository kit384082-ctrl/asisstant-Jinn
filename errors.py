"""Structured, actionable errors shared by backend API boundaries."""

from __future__ import annotations


class ActionableError(RuntimeError):
    """An error with a stable machine code and a safe user-facing recovery step."""

    def __init__(self, code: str, message: str, solution: str) -> None:
        super().__init__(message)
        self.code = code
        self.solution = solution


_GENERIC_SOLUTIONS = {
    "ru": {
        "BAD_REQUEST": "Проверьте введённые данные и повторите запрос.",
        "FORBIDDEN_LOCAL_ONLY": "Откройте Jinn через localhost на том компьютере, где запущен агент.",
        "REQUEST_TOO_LARGE": "Сократите текст или размер отправляемых настроек.",
        "UNSUPPORTED_MEDIA_TYPE": "Отправьте JSON с заголовком Content-Type: application/json.",
        "RATE_LIMITED": "Подождите немного и повторите запрос.",
        "UPSTREAM_ERROR": "Проверьте ключ, модель, базовый URL и доступность выбранного внешнего сервиса.",
        "INTERNAL_ERROR": "Повторите запрос. Если ошибка сохраняется, проверьте журнал сервера.",
    },
    "en": {
        "BAD_REQUEST": "Check the entered data and try again.",
        "FORBIDDEN_LOCAL_ONLY": "Open Jinn through localhost on the computer running the agent.",
        "REQUEST_TOO_LARGE": "Shorten the text or reduce the submitted settings.",
        "UNSUPPORTED_MEDIA_TYPE": "Send JSON with Content-Type: application/json.",
        "RATE_LIMITED": "Wait briefly, then try again.",
        "UPSTREAM_ERROR": "Check the key, model, base URL, and availability of the selected external service.",
        "INTERNAL_ERROR": "Try again. If the error persists, inspect the server log.",
    },
    "de": {
        "BAD_REQUEST": "Prüfe die eingegebenen Daten und versuche es erneut.",
        "FORBIDDEN_LOCAL_ONLY": "Öffne Jinn über localhost auf dem Computer, auf dem der Agent läuft.",
        "REQUEST_TOO_LARGE": "Kürze den Text oder die gesendeten Einstellungen.",
        "UNSUPPORTED_MEDIA_TYPE": "Sende JSON mit Content-Type: application/json.",
        "RATE_LIMITED": "Warte kurz und versuche es erneut.",
        "UPSTREAM_ERROR": "Prüfe Schlüssel, Modell, Basis-URL und Erreichbarkeit des gewählten externen Dienstes.",
        "INTERNAL_ERROR": "Versuche es erneut. Bleibt der Fehler bestehen, prüfe das Serverprotokoll.",
    },
    "es": {
        "BAD_REQUEST": "Comprueba los datos introducidos e inténtalo de nuevo.",
        "FORBIDDEN_LOCAL_ONLY": "Abre Jinn mediante localhost en el equipo donde se ejecuta el agente.",
        "REQUEST_TOO_LARGE": "Acorta el texto o reduce los ajustes enviados.",
        "UNSUPPORTED_MEDIA_TYPE": "Envía JSON con Content-Type: application/json.",
        "RATE_LIMITED": "Espera un momento y vuelve a intentarlo.",
        "UPSTREAM_ERROR": "Comprueba la clave, el modelo, la URL base y la disponibilidad del servicio externo elegido.",
        "INTERNAL_ERROR": "Inténtalo de nuevo. Si continúa, revisa el registro del servidor.",
    },
    "fr": {
        "BAD_REQUEST": "Vérifiez les données saisies puis réessayez.",
        "FORBIDDEN_LOCAL_ONLY": "Ouvrez Jinn via localhost sur l’ordinateur qui exécute l’agent.",
        "REQUEST_TOO_LARGE": "Raccourcissez le texte ou réduisez les réglages envoyés.",
        "UNSUPPORTED_MEDIA_TYPE": "Envoyez du JSON avec Content-Type: application/json.",
        "RATE_LIMITED": "Patientez un instant puis réessayez.",
        "UPSTREAM_ERROR": "Vérifiez la clé, le modèle, l’URL de base et la disponibilité du service externe choisi.",
        "INTERNAL_ERROR": "Réessayez. Si l’erreur persiste, consultez le journal du serveur.",
    },
}


def normalize_error_language(language: str | None) -> str:
    code = (language or "ru").split("-", 1)[0].casefold()
    return code if code in _GENERIC_SOLUTIONS else "ru"


def solution_for(code: str, language: str | None = None) -> str:
    locale = normalize_error_language(language)
    return _GENERIC_SOLUTIONS[locale].get(
        code, _GENERIC_SOLUTIONS[locale]["BAD_REQUEST"]
    )

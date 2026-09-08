"""Language metadata and small deterministic UI translations."""

from typing import Final

SUPPORTED_LANGUAGES: Final[tuple[str, ...]] = (
    "English",
    "हिंदी",
    "বাংলা",
    "मराठी",
    "தமிழ்",
    "తెలుగు",
)

LANGUAGE_LOCALES: Final[dict[str, str]] = {
    "English": "en-IN",
    "हिंदी": "hi-IN",
    "বাংলা": "bn-IN",
    "मराठी": "mr-IN",
    "தமிழ்": "ta-IN",
    "తెలుగు": "te-IN",
}


def language_locale(language: str) -> str:
    """Return a browser/recognition locale, defaulting safely to English."""
    return LANGUAGE_LOCALES.get(language, "en-IN")


def language_label(language: str, english: str, hindi: str) -> str:
    """Keep existing English/Hindi wording while adding a safe fallback label."""
    if language == "हिंदी":
        return hindi
    return english

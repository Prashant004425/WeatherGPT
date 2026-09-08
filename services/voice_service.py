"""Optional speech input and browser speech output helpers."""

from __future__ import annotations

from typing import Any


def transcribe_audio(audio: Any, language: str) -> tuple[str | None, str | None]:
    """Transcribe a Streamlit WAV recording when SpeechRecognition is installed."""
    if audio is None:
        return None, None
    try:
        import speech_recognition as sr
    except ImportError:
        return None, "Voice transcription is optional. Install SpeechRecognition to enable it."

    recognizer = sr.Recognizer()
    try:
        audio.seek(0)
        with sr.AudioFile(audio) as source:
            recording = recognizer.record(source)
        text = recognizer.recognize_google(recording, language=language)
    except (OSError, ValueError, sr.RequestError, sr.UnknownValueError) as exc:
        if isinstance(exc, sr.UnknownValueError):
            return None, "We could not understand that recording. Please try again or type your question."
        if isinstance(exc, sr.RequestError):
            return None, "Speech recognition is temporarily unavailable. Please type your question."
        return None, "That recording could not be processed. Please try again or type your question."
    return (text.strip() or None), None


def browser_speech_script(text: str, locale: str) -> str:
    """Return a self-contained browser TTS snippet; failures stay in the browser."""
    import json

    return f"""
    <script>
    (() => {{
      const text = {json.dumps(text)};
      const locale = {json.dumps(locale)};
      if (!("speechSynthesis" in window) || !text) return;
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = locale;
      window.speechSynthesis.speak(utterance);
    }})();
    </script>
    """

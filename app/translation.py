import os

import requests
from flask import current_app


LANG_NAMES = {
    "es": {"es": "español", "en": "Spanish"},
    "en": {"es": "inglés", "en": "English"},
}


def language_name(code, ui_lang="es"):
    return LANG_NAMES.get(code, {}).get(ui_lang, code or "")


def translate_text(text, source_lang, target_lang):
    """
    Translate text using an optional LibreTranslate-compatible endpoint.
    Configure with:
      ADCRITIC_TRANSLATE_URL=https://...
      ADCRITIC_TRANSLATE_API_KEY=...
      ADCRITIC_TRANSLATE_PROVIDER=LibreTranslate
    Returns (translated_text, provider_name) or (None, None).
    """
    text = (text or "").strip()
    if not text or source_lang == target_lang:
        return None, None

    url = os.environ.get("ADCRITIC_TRANSLATE_URL", "").strip()
    if not url:
        return None, None

    provider = os.environ.get("ADCRITIC_TRANSLATE_PROVIDER", "LibreTranslate").strip()
    payload = {
        "q": text,
        "source": source_lang,
        "target": target_lang,
        "format": "text",
    }
    api_key = os.environ.get("ADCRITIC_TRANSLATE_API_KEY", "").strip()
    if api_key:
        payload["api_key"] = api_key

    try:
        res = requests.post(url.rstrip("/") + "/translate", json=payload, timeout=12)
        res.raise_for_status()
        data = res.json()
        translated = (data.get("translatedText") or "").strip()
        return (translated, provider) if translated else (None, None)
    except Exception as exc:
        current_app.logger.warning(f"Comment translation failed: {exc}")
        return None, None

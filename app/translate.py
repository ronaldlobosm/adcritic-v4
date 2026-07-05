"""
app/translate.py — Machine translation for the bio field via the Google
Cloud Translation API (Basic/v2, authenticated with a plain API key).
"""
import os

import requests

TRANSLATE_URL = "https://translation.googleapis.com/language/translate/v2"


def translate_text(text, source, target):
    """
    Translate `text` from `source` to `target` ('es'/'en').
    Returns the translated string, or None if translation is unavailable
    or fails — callers should treat that as "leave the field blank" rather
    than a hard error, since a bio translation is a nice-to-have, not
    something that should block saving a profile.
    """
    if not text:
        return None

    api_key = os.environ.get("GOOGLE_TRANSLATE_API_KEY", "")
    if not api_key:
        return None

    try:
        resp = requests.post(
            TRANSLATE_URL,
            params={"key": api_key},
            json={"q": text, "source": source, "target": target, "format": "text"},
            timeout=8,
        )
        resp.raise_for_status()
        return resp.json()["data"]["translations"][0]["translatedText"]
    except (requests.RequestException, KeyError, IndexError, ValueError):
        return None

"""
app/translate.py — Machine translation for the bio field via the Google
Cloud Translation API (Basic/v2, authenticated with a plain API key).
"""
import logging
import os

import requests

TRANSLATE_URL = "https://translation.googleapis.com/language/translate/v2"

logger = logging.getLogger(__name__)


def translate_text(text, source, target, fmt="text"):
    """
    Translate `text` from `source` to `target` ('es'/'en').
    Pass fmt="html" for rich-text bodies so Google translates the text
    nodes and leaves the surrounding tags intact instead of treating the
    markup as literal words to translate.
    Returns the translated string, or None if translation is unavailable
    or fails — callers should treat that as "leave the field blank" rather
    than a hard error, since a bio translation is a nice-to-have, not
    something that should block saving a profile.
    """
    if not text:
        return None

    api_key = os.environ.get("GOOGLE_TRANSLATE_API_KEY", "")
    if not api_key:
        logger.warning("[translate] GOOGLE_TRANSLATE_API_KEY is not set — skipping translation")
        return None

    try:
        resp = requests.post(
            TRANSLATE_URL,
            params={"key": api_key},
            json={"q": text, "source": source, "target": target, "format": fmt},
            timeout=8,
        )
        resp.raise_for_status()
        return resp.json()["data"]["translations"][0]["translatedText"]
    except requests.RequestException as exc:
        body = exc.response.text[:300] if exc.response is not None else str(exc)
        logger.error(f"[translate] Google Translate API call failed: {body}")
        return None
    except (KeyError, IndexError, ValueError) as exc:
        logger.error(f"[translate] Unexpected Google Translate response shape: {exc}")
        return None

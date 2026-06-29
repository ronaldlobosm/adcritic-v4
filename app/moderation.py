import re


def contains_banned_word(text):
    """Whole-word match, case-insensitive, Unicode-aware."""
    from app.models import BannedWord
    text_lower = text.lower()
    for bw in BannedWord.query.all():
        pattern = re.compile(
            r'\b' + re.escape(bw.word.lower()) + r'\b',
            re.IGNORECASE | re.UNICODE,
        )
        if pattern.search(text_lower):
            return True
    return False


def comment_status_for_text(text):
    """Returns 'pending' if text has a banned word, 'approved' otherwise."""
    return 'pending' if contains_banned_word(text) else 'approved'

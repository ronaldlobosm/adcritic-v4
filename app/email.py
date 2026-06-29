"""
app/email.py — Transactional email helpers for AdCritic.
"""
import secrets
import string
from datetime import datetime

from flask import current_app, render_template, url_for
from flask_mail import Message

from app import mail, db


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _generate_code(length=6):
    """Return a numeric string of `length` digits."""
    return "".join(secrets.choice(string.digits) for _ in range(length))


# ---------------------------------------------------------------------------
# Email verification
# ---------------------------------------------------------------------------

def send_verification_email(user, lang="es"):
    """
    Generate a 6-digit code + URL-safe token, persist them on the user,
    and send a bilingual verification email with both options.

    Must be called inside a request context (so url_for works).
    Returns (True, None) on success or (False, error_message) on failure.
    """
    code  = _generate_code()
    token = secrets.token_urlsafe(40)

    user.email_verify_code    = code
    user.email_verify_token   = token
    user.email_verify_sent_at = datetime.utcnow()
    db.session.commit()

    if lang == "es":
        verify_link = url_for("auth.verify_link_es", token=token, _external=True)
        verify_page = url_for("auth.verify_page_es", _external=True)
        subject     = "Confirma tu correo en AdCritic"
    else:
        verify_link = url_for("auth.verify_link_en", token=token, _external=True)
        verify_page = url_for("auth.verify_page_en", _external=True)
        subject     = "Verify your email on AdCritic"

    html = render_template(
        f"email/verify_{lang}.html",
        user=user,
        code=code,
        verify_link=verify_link,
        verify_page=verify_page,
    )

    sender = current_app.config.get(
        "MAIL_DEFAULT_SENDER", "AdCritic <noreply@adcritic.com>"
    )
    msg = Message(subject=subject, recipients=[user.email],
                  html=html, sender=sender)
    try:
        mail.send(msg)
        return True, None
    except Exception as exc:
        current_app.logger.error(
            f"[email] Failed to send to {user.email}: {exc}"
        )
        return False, str(exc)

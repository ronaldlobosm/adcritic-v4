"""
cleanup_unverified.py — Delete accounts that haven't verified email within 7 days.

Run manually or as a daily cron:
    venv/bin/python cleanup_unverified.py

The script is safe to run multiple times (idempotent).
Only accounts with ALL of the following are deleted:
  - email_verified = False
  - email_verify_sent_at is not NULL (i.e. the verification email was actually sent)
  - email_verify_sent_at < now - 7 days
"""
import os
import sys
from datetime import datetime, timedelta

# ── Add project root to path so 'app' is importable ─────────────────────────
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models import User

DAYS = 7


def cleanup():
    app = create_app()
    with app.app_context():
        cutoff = datetime.utcnow() - timedelta(days=DAYS)

        to_delete = User.query.filter(
            User.email_verified      == False,           # noqa: E712
            User.email_verify_sent_at != None,           # noqa: E711
            User.email_verify_sent_at < cutoff,
        ).all()

        if not to_delete:
            print("cleanup_unverified: nothing to delete.")
            return

        for user in to_delete:
            age = (datetime.utcnow() - user.email_verify_sent_at).days
            print(f"  Deleting user {user.id} <{user.email}>"
                  f" — verification email sent {age}d ago")
            db.session.delete(user)

        db.session.commit()
        print(f"cleanup_unverified: deleted {len(to_delete)} unverified account(s).")


if __name__ == "__main__":
    cleanup()

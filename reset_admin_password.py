"""Reset or create the admin user from environment variables.

This is intentionally env-gated so production can rotate the admin password
without hardcoding credentials in the repository.
"""
import os

from app import db
from app.models import User
from run import app


def main():
    email = os.environ.get("ADMIN_EMAIL", "admin@adcritic.com").strip().lower()
    password = os.environ.get("ADMIN_RESET_PASSWORD", "").strip()

    if not password:
        print("[admin-reset] ADMIN_RESET_PASSWORD not set; skipping")
        return

    if len(password) < 8:
        raise SystemExit("[admin-reset] ADMIN_RESET_PASSWORD must be at least 8 characters")

    with app.app_context():
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(email=email)
            db.session.add(user)

        user.role = "admin"
        user.is_active = True
        user.email_verified = True
        user.set_password(password)
        db.session.commit()
        print(f"[admin-reset] admin password reset for {email}")


if __name__ == "__main__":
    main()

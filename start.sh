#!/bin/bash
set -e

echo ">>> FLASK_ENV=${FLASK_ENV}"
echo ">>> DATABASE_URL prefix: ${DATABASE_URL:0:30}..."

python - <<'PYEOF'
import os, sys

print(f"[init] FLASK_ENV      = {os.environ.get('FLASK_ENV', 'NOT SET')}")
print(f"[init] DATABASE_URL   = {os.environ.get('DATABASE_URL', 'NOT SET')[:40]}...")

from run import app
from app import db

# Explicit import of every model so SQLAlchemy knows all tables
from app.models import (
    User, Category, PostCategory, MediaFile,
    Ad, AdTranslation, AdComment, AdCommentLike, AdCommentRating, SavedAd,
    Post, PostTranslation, PostComment,
    NewsletterSubscriber, SiteSettings, RoleContentAccess, BannedWord,
    Advertiser, AdCampaign, AdZone, BannerAd,
)

with app.app_context():
    uri = app.config.get("SQLALCHEMY_DATABASE_URI") or "NONE"
    print(f"[init] DB URI         = {uri[:50]}...")

    if "sqlite" in uri:
        print("[init] ERROR: using SQLite — DATABASE_URL or FLASK_ENV not set correctly", file=sys.stderr)
        sys.exit(1)

    db.create_all()

    from sqlalchemy import inspect as sqla_inspect
    tables = sorted(sqla_inspect(db.engine).get_table_names())
    print(f"[init] Tables in DB   = {tables}")

    if "ads" not in tables:
        print("[init] ERROR: 'ads' table missing after create_all!", file=sys.stderr)
        sys.exit(1)

    print("[init] DB OK — all tables present")

    # ── Column migrations (idempotent) ──────────────────────────────────
    from sqlalchemy import text
    with db.engine.connect() as conn:
        existing = [r[0] for r in conn.execute(
            text("SELECT column_name FROM information_schema.columns WHERE table_name='users'")
        )]
        for col, ddl in [
            ("first_name", "ALTER TABLE users ADD COLUMN first_name VARCHAR(80)"),
            ("last_name",  "ALTER TABLE users ADD COLUMN last_name  VARCHAR(80)"),
            ("password_reset_token", "ALTER TABLE users ADD COLUMN password_reset_token VARCHAR(100) UNIQUE"),
            ("password_reset_sent_at", "ALTER TABLE users ADD COLUMN password_reset_sent_at TIMESTAMP"),
            ("linkedin_url", "ALTER TABLE users ADD COLUMN linkedin_url VARCHAR(300)"),
            ("location", "ALTER TABLE users ADD COLUMN location VARCHAR(120)"),
            ("preferred_language", "ALTER TABLE users ADD COLUMN preferred_language VARCHAR(2)"),
            ("other_languages", "ALTER TABLE users ADD COLUMN other_languages VARCHAR(200)"),
        ]:
            if col not in existing:
                conn.execute(text(ddl))
                conn.commit()
                print(f"[init] Added column users.{col}")

        media_existing = [r[0] for r in conn.execute(
            text("SELECT column_name FROM information_schema.columns WHERE table_name='media_files'")
        )]
        for col, ddl in [
            ("remote_url", "ALTER TABLE media_files ADD COLUMN remote_url VARCHAR(700)"),
            ("thumbnail_remote_url", "ALTER TABLE media_files ADD COLUMN thumbnail_remote_url VARCHAR(700)"),
            ("cloudinary_public_id", "ALTER TABLE media_files ADD COLUMN cloudinary_public_id VARCHAR(300)"),
            ("thumbnail_cloudinary_public_id", "ALTER TABLE media_files ADD COLUMN thumbnail_cloudinary_public_id VARCHAR(300)"),
        ]:
            if col not in media_existing:
                conn.execute(text(ddl))
                conn.commit()
                print(f"[init] Added column media_files.{col}")
PYEOF

echo ">>> Seeding news posts..."
python seed_news.py

echo ">>> Checking admin password reset..."
python reset_admin_password.py

echo ">>> Starting gunicorn..."
exec gunicorn run:app

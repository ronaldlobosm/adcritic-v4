"""Add video source fields, subtitle fields, media_files table, and create upload dirs."""
import os
from app import create_app, db
from sqlalchemy import text

app = create_app()

ALTERS = [
    # Ad
    "ALTER TABLE ads ADD COLUMN video_source_type VARCHAR(20)",
    "ALTER TABLE ads ADD COLUMN video_source_value VARCHAR(500)",
    "ALTER TABLE ads ADD COLUMN subtitle_es VARCHAR(300)",
    "ALTER TABLE ads ADD COLUMN subtitle_en VARCHAR(300)",
    # Post
    "ALTER TABLE posts ADD COLUMN video_source_type VARCHAR(20)",
    "ALTER TABLE posts ADD COLUMN video_source_value VARCHAR(500)",
    "ALTER TABLE posts ADD COLUMN subtitle_es VARCHAR(300)",
    "ALTER TABLE posts ADD COLUMN subtitle_en VARCHAR(300)",
]

DATA_MIGRATIONS = [
    # Migrate existing youtube_id → new fields for ads
    "UPDATE ads SET video_source_type='youtube', video_source_value=youtube_id WHERE youtube_id != '' AND video_source_type IS NULL",
    # Migrate existing youtube_id → new fields for posts
    "UPDATE posts SET video_source_type='youtube', video_source_value=youtube_id WHERE youtube_id IS NOT NULL AND youtube_id != '' AND video_source_type IS NULL",
]

with app.app_context():
    for stmt in ALTERS:
        col = stmt.split("COLUMN")[1].strip().split()[0]
        table = stmt.split("TABLE")[1].strip().split()[0]
        try:
            db.session.execute(text(stmt))
            db.session.commit()
            print(f"  Added {table}.{col}")
        except Exception as e:
            db.session.rollback()
            if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                print(f"  Skipped {table}.{col} (exists)")
            else:
                print(f"  ERROR on {table}.{col}: {e}")

    for stmt in DATA_MIGRATIONS:
        try:
            db.session.execute(text(stmt))
            db.session.commit()
            print(f"  Data migration OK: {stmt[:60]}...")
        except Exception as e:
            db.session.rollback()
            print(f"  ERROR data migration: {e}")

    db.create_all()
    print("  media_files table ready")

    # Create upload directories
    from config import UPLOAD_BASE
    for sub in ("images", "videos", "subtitles"):
        path = os.path.join(UPLOAD_BASE, sub)
        os.makedirs(path, exist_ok=True)
        print(f"  Directory: {path}")

    print("Done.")

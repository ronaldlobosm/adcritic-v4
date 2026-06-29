"""Add new columns and site_settings table."""
from app import create_app, db
from sqlalchemy import text

app = create_app()

ALTERS = [
    "ALTER TABLE ad_translations ADD COLUMN meta_title VARCHAR(200)",
    "ALTER TABLE ad_translations ADD COLUMN meta_description VARCHAR(300)",
    "ALTER TABLE posts ADD COLUMN youtube_id VARCHAR(20)",
    "ALTER TABLE post_translations ADD COLUMN meta_title VARCHAR(250)",
    "ALTER TABLE post_translations ADD COLUMN meta_description VARCHAR(300)",
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

    # Create new tables (no-op if already exist)
    db.create_all()
    print("  site_settings table ready")
    print("Done.")

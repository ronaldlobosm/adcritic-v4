"""
migrate4.py — adds thumbnail + metadata columns to media_files table.
Run once: python3 migrate4.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db

app = create_app("development")

COLUMNS = [
    "ALTER TABLE media_files ADD COLUMN thumbnail    VARCHAR(300)",
    "ALTER TABLE media_files ADD COLUMN title_es     VARCHAR(300)",
    "ALTER TABLE media_files ADD COLUMN title_en     VARCHAR(300)",
    "ALTER TABLE media_files ADD COLUMN alt_text_es  VARCHAR(300)",
    "ALTER TABLE media_files ADD COLUMN alt_text_en  VARCHAR(300)",
    "ALTER TABLE media_files ADD COLUMN description  TEXT",
]

with app.app_context():
    with db.engine.connect() as conn:
        for sql in COLUMNS:
            col = sql.split("ADD COLUMN")[1].strip().split()[0]
            try:
                conn.execute(db.text(sql))
                conn.commit()
                print(f"  added: {col}")
            except Exception as e:
                if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                    print(f"  skip (exists): {col}")
                else:
                    print(f"  ERROR on {col}: {e}")
    print("migrate4 done.")

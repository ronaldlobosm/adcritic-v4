"""
migrate11.py — Add bilingual translation fields for ad critiques.
Run once: venv/bin/python migrate11.py
"""
import os
import sqlite3

DB = os.path.join(os.path.dirname(__file__), "adcritic.db")
conn = sqlite3.connect(DB)
cur = conn.cursor()

alterations = [
    "ALTER TABLE ad_comments ADD COLUMN body_language VARCHAR(5) NOT NULL DEFAULT 'es'",
    "ALTER TABLE ad_comments ADD COLUMN translated_body TEXT",
    "ALTER TABLE ad_comments ADD COLUMN translated_language VARCHAR(5)",
    "ALTER TABLE ad_comments ADD COLUMN translation_provider VARCHAR(80)",
]

for sql in alterations:
    try:
        cur.execute(sql)
        print(f"OK  {sql}")
    except sqlite3.OperationalError as e:
        print(f"SKP {e}")

conn.commit()
conn.close()
print("migrate11 done.")

"""
migrate10.py — Add Gold critic profile and ad critique ratings.
Run once: venv/bin/python migrate10.py
"""
import os
import sqlite3

DB = os.path.join(os.path.dirname(__file__), "adcritic.db")
conn = sqlite3.connect(DB)
cur = conn.cursor()

alterations = [
    "ALTER TABLE users ADD COLUMN professional_title VARCHAR(140)",
    "ALTER TABLE ad_comments ADD COLUMN rating_music INTEGER",
    "ALTER TABLE ad_comments ADD COLUMN rating_art_direction INTEGER",
    "ALTER TABLE ad_comments ADD COLUMN rating_copywriting INTEGER",
    "ALTER TABLE ad_comments ADD COLUMN rating_strategy INTEGER",
]

for sql in alterations:
    try:
        cur.execute(sql)
        print(f"OK  {sql}")
    except sqlite3.OperationalError as e:
        print(f"SKP {e}")

conn.commit()
conn.close()
print("migrate10 done.")

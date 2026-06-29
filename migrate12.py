"""
migrate12.py — Enforce one ad critique per user per ad.
Run once: venv/bin/python migrate12.py
"""
import os
import sqlite3

DB = os.path.join(os.path.dirname(__file__), "adcritic.db")
conn = sqlite3.connect(DB)
cur = conn.cursor()

try:
    cur.execute("""
        DELETE FROM ad_comments
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM ad_comments
            GROUP BY ad_id, user_id
        )
    """)
    print(f"Removed duplicate critiques: {cur.rowcount}")
    cur.execute(
        "CREATE UNIQUE INDEX uq_ad_comments_ad_user ON ad_comments (ad_id, user_id)"
    )
    print("OK  CREATE UNIQUE INDEX uq_ad_comments_ad_user")
except sqlite3.OperationalError as e:
    print(f"SKP {e}")

conn.commit()
conn.close()
print("migrate12 done.")

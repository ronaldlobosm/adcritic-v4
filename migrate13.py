"""
migrate13.py — Add Gold critique access window fields.
Run once: venv/bin/python migrate13.py
"""
import os
import sqlite3
from datetime import datetime

DB = os.path.join(os.path.dirname(__file__), "adcritic.db")
conn = sqlite3.connect(DB)
cur = conn.cursor()

alterations = [
    "ALTER TABLE users ADD COLUMN gold_started_at DATETIME",
    "ALTER TABLE users ADD COLUMN gold_intro_critique_used BOOLEAN NOT NULL DEFAULT 0",
]

for sql in alterations:
    try:
        cur.execute(sql)
        print(f"OK  {sql}")
    except sqlite3.OperationalError as e:
        print(f"SKP {e}")

now = datetime.utcnow().isoformat(sep=" ")
cur.execute(
    "UPDATE users SET gold_started_at = COALESCE(gold_started_at, ?) WHERE role = 'gold'",
    (now,),
)
print(f"Gold start stamped: {cur.rowcount}")

cur.execute("""
    UPDATE users
    SET gold_intro_critique_used = 1
    WHERE role = 'gold'
      AND id IN (SELECT DISTINCT user_id FROM ad_comments)
""")
print(f"Gold intro marked used for prior critics: {cur.rowcount}")

conn.commit()
conn.close()
print("migrate13 done.")

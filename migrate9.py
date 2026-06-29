"""
migrate9.py — Add email verification fields to users table
Run once: venv/bin/python migrate9.py
"""
import sqlite3, os

DB = os.path.join(os.path.dirname(__file__), "adcritic.db")
conn = sqlite3.connect(DB)
cur  = conn.cursor()

alterations = [
    "ALTER TABLE users ADD COLUMN email_verified      BOOLEAN NOT NULL DEFAULT 0",
    "ALTER TABLE users ADD COLUMN email_verify_token  VARCHAR(100)",
    "ALTER TABLE users ADD COLUMN email_verify_code   VARCHAR(6)",
    "ALTER TABLE users ADD COLUMN email_verify_sent_at DATETIME",
]

for sql in alterations:
    try:
        cur.execute(sql)
        print(f"OK  {sql}")
    except sqlite3.OperationalError as e:
        print(f"SKP {e}")

# Existing users (staff/admin) are pre-verified
cur.execute("""
    UPDATE users SET email_verified = 1
    WHERE role IN ('admin', 'editor', 'approver', 'advertiser')
""")
print(f"Pre-verified {cur.rowcount} staff user(s).")

conn.commit()
conn.close()
print("migrate9 done.")

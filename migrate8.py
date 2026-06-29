"""
migrate8.py — Add Stripe subscription fields to users table
Run once: venv/bin/python migrate8.py
"""
import sqlite3, os

DB = os.path.join(os.path.dirname(__file__), "adcritic.db")
conn = sqlite3.connect(DB)
cur  = conn.cursor()

alterations = [
    "ALTER TABLE users ADD COLUMN stripe_customer_id     VARCHAR(100)",
    "ALTER TABLE users ADD COLUMN stripe_subscription_id VARCHAR(100)",
    "ALTER TABLE users ADD COLUMN stripe_price_id        VARCHAR(100)",
]

for sql in alterations:
    try:
        cur.execute(sql)
        print(f"OK  {sql}")
    except sqlite3.OperationalError as e:
        print(f"SKP {e}")

conn.commit()
conn.close()
print("migrate8 done.")

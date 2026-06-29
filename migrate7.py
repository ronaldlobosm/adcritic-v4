"""migrate7.py — Ad comments + is_premium on ads"""
import sqlite3, os

DB_PATH = os.path.join(os.path.dirname(__file__), "adcritic.db")
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# 1. Add is_premium to ads
try:
    cur.execute("ALTER TABLE ads ADD COLUMN is_premium BOOLEAN NOT NULL DEFAULT 0")
    print("✓ Added is_premium to ads")
except sqlite3.OperationalError as e:
    print(f"  is_premium: {e}")

# 2. Create ad_comments table
cur.execute("""
CREATE TABLE IF NOT EXISTS ad_comments (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    ad_id      INTEGER NOT NULL REFERENCES ads(id),
    user_id    INTEGER NOT NULL REFERENCES users(id),
    body       TEXT NOT NULL,
    status     VARCHAR(20) NOT NULL DEFAULT 'approved',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")
print("✓ Created ad_comments table")

conn.commit()
conn.close()
print("migrate7.py done")

import sqlite3

DB = "adcritic.db"


def column_exists(cur, table, column):
    cur.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cur.fetchall())


conn = sqlite3.connect(DB)
cur = conn.cursor()

if not column_exists(cur, "ads", "is_featured"):
    cur.execute("ALTER TABLE ads ADD COLUMN is_featured BOOLEAN NOT NULL DEFAULT 0")
    print("Added ads.is_featured")
else:
    print("ads.is_featured already exists")

conn.commit()
conn.close()

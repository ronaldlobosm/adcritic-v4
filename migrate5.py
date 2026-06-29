"""
Migration 5 — User profile, RoleContentAccess, Ad/Post workflow status.

Safe to re-run: checks for existing columns/tables before altering.
"""
import os, sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "adcritic.db")
conn = sqlite3.connect(DB_PATH)
cur  = conn.cursor()


def col_exists(table, col):
    cur.execute(f"PRAGMA table_info({table})")
    return any(r[1] == col for r in cur.fetchall())


# ------------------------------------------------------------------
# 1. User: public profile columns
# ------------------------------------------------------------------
profile_cols = [
    ("display_name",    "TEXT"),
    ("avatar_media_id", "INTEGER REFERENCES media_files(id)"),
    ("bio_es",          "TEXT"),
    ("bio_en",          "TEXT"),
]
for col, defn in profile_cols:
    if not col_exists("users", col):
        cur.execute(f"ALTER TABLE users ADD COLUMN {col} {defn}")
        print(f"  users.{col} added")

# ------------------------------------------------------------------
# 2. RoleContentAccess table
# ------------------------------------------------------------------
cur.execute("""
CREATE TABLE IF NOT EXISTS role_content_access (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL REFERENCES users(id),
    content_type TEXT    NOT NULL,
    section_id   INTEGER,
    UNIQUE (user_id, content_type)
)
""")
print("  role_content_access table: OK")

# ------------------------------------------------------------------
# 3. Ad: workflow columns
# ------------------------------------------------------------------
ad_cols = [
    ("status",         "TEXT NOT NULL DEFAULT 'published'"),
    ("rejection_note", "TEXT"),
    ("created_by_id",  "INTEGER REFERENCES users(id)"),
]
for col, defn in ad_cols:
    if not col_exists("ads", col):
        cur.execute(f"ALTER TABLE ads ADD COLUMN {col} {defn}")
        print(f"  ads.{col} added")

# ------------------------------------------------------------------
# 4. Post: workflow columns
# ------------------------------------------------------------------
post_cols = [
    ("status",         "TEXT NOT NULL DEFAULT 'published'"),
    ("rejection_note", "TEXT"),
]
for col, defn in post_cols:
    if not col_exists("posts", col):
        cur.execute(f"ALTER TABLE posts ADD COLUMN {col} {defn}")
        print(f"  posts.{col} added")

# ------------------------------------------------------------------
# 5. Seed status = 'published' for all existing rows
#    (rows added before this migration have NULL in the new column
#     when SQLite ignores DEFAULT on ALTER TABLE in older versions)
# ------------------------------------------------------------------
cur.execute("UPDATE ads  SET status = 'published' WHERE status IS NULL OR status = ''")
cur.execute("UPDATE posts SET status = 'published' WHERE status IS NULL OR status = ''")
print("  existing ads/posts seeded as 'published'")

conn.commit()
conn.close()
print("Migration 5 complete.")

"""
migrate16.py — Add views_count to posts + sidebar_news_lower ad zone
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import sqlite3

DB = os.path.join(os.path.dirname(__file__), "adcritic.db")
conn = sqlite3.connect(DB)
cur = conn.cursor()

# 1. views_count on posts (safe: only if column doesn't exist)
cols = [r[1] for r in cur.execute("PRAGMA table_info(posts)").fetchall()]
if "views_count" not in cols:
    cur.execute("ALTER TABLE posts ADD COLUMN views_count INTEGER NOT NULL DEFAULT 0")
    print("  + posts.views_count added")
else:
    print("  ~ posts.views_count already exists")

# 2. New ad zone
existing = cur.execute("SELECT zone_key FROM ad_zones WHERE zone_key='sidebar_news_lower'").fetchone()
if not existing:
    cur.execute("""
        INSERT INTO ad_zones (zone_key, display_name, description, width, height)
        VALUES ('sidebar_news_lower', 'Sidebar noticias inferior', 'Segundo banner en sidebar de noticias', 300, 250)
    """)
    print("  + ad_zones: sidebar_news_lower added")
else:
    print("  ~ sidebar_news_lower already exists")

conn.commit()
conn.close()
print("Done.")

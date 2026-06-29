"""migrate17 — Add ad_campaigns table + name/campaign_id to banner_ads"""
import sqlite3, os, sys
sys.path.insert(0, os.path.dirname(__file__))

DB = os.path.join(os.path.dirname(__file__), "adcritic.db")
conn = sqlite3.connect(DB)
cur = conn.cursor()

# 1. ad_campaigns table
cur.execute("""
    CREATE TABLE IF NOT EXISTS ad_campaigns (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        advertiser_id INTEGER REFERENCES advertisers(id) ON DELETE SET NULL,
        name          TEXT NOT NULL,
        is_active     INTEGER NOT NULL DEFAULT 1,
        created_at    TEXT DEFAULT (datetime('now'))
    )
""")
print("  + ad_campaigns table ready")

# 2. banner_ads: name column
cols = [r[1] for r in cur.execute("PRAGMA table_info(banner_ads)").fetchall()]
if "name" not in cols:
    cur.execute("ALTER TABLE banner_ads ADD COLUMN name TEXT")
    print("  + banner_ads.name added")
if "campaign_id" not in cols:
    cur.execute("ALTER TABLE banner_ads ADD COLUMN campaign_id INTEGER REFERENCES ad_campaigns(id) ON DELETE SET NULL")
    print("  + banner_ads.campaign_id added")

conn.commit()
conn.close()
print("Done.")

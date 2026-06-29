"""migrate18 — Add category to ad_campaigns; geo fields to banner_ads"""
import sqlite3, os, sys
sys.path.insert(0, os.path.dirname(__file__))

DB = os.path.join(os.path.dirname(__file__), "adcritic.db")
conn = sqlite3.connect(DB)
cur = conn.cursor()

cols_camp = [r[1] for r in cur.execute("PRAGMA table_info(ad_campaigns)").fetchall()]
if "category" not in cols_camp:
    cur.execute("ALTER TABLE ad_campaigns ADD COLUMN category TEXT")
    print("  + ad_campaigns.category")

cols_ban = [r[1] for r in cur.execute("PRAGMA table_info(banner_ads)").fetchall()]
if "target_countries" not in cols_ban:
    cur.execute("ALTER TABLE banner_ads ADD COLUMN target_countries TEXT")
    print("  + banner_ads.target_countries")
if "blocked_countries" not in cols_ban:
    cur.execute("ALTER TABLE banner_ads ADD COLUMN blocked_countries TEXT")
    print("  + banner_ads.blocked_countries")

conn.commit()
conn.close()
print("Done.")

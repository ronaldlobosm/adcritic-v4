"""
migrate15.py — Advertising/banner system tables.

Creates: advertisers, ad_zones, banner_ads
Seeds:   3 initial ad zones (header_banner, catalog_inline, sidebar_news)
"""
import sqlite3, os

DB = os.path.join(os.path.dirname(__file__), "adcritic.db")

ZONES = [
    ("header_banner",   "Banner superior",      "Banner horizontal debajo del header, visible en todas las páginas", 970, 90),
    ("catalog_inline",  "Banner entre críticas", "Banner insertado entre las tarjetas del catálogo de críticas",     728, 90),
    ("sidebar_news",    "Sidebar de noticias",   "Banner en la columna lateral de la sección de noticias",           300, 250),
]

def run():
    con = sqlite3.connect(DB)
    cur = con.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS advertisers (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name  TEXT    NOT NULL,
            contact_name  TEXT,
            contact_email TEXT,
            is_active     INTEGER NOT NULL DEFAULT 1,
            created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS ad_zones (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            zone_key     TEXT    NOT NULL UNIQUE,
            display_name TEXT    NOT NULL,
            description  TEXT,
            width        INTEGER,
            height       INTEGER
        );

        CREATE TABLE IF NOT EXISTS banner_ads (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            advertiser_id     INTEGER REFERENCES advertisers(id),
            zone_id           INTEGER NOT NULL REFERENCES ad_zones(id),
            ad_type           TEXT    NOT NULL DEFAULT 'image',
            content           TEXT    NOT NULL,
            click_url         TEXT,
            start_date        DATE,
            end_date          DATE,
            is_active         INTEGER NOT NULL DEFAULT 1,
            impressions_count INTEGER NOT NULL DEFAULT 0,
            clicks_count      INTEGER NOT NULL DEFAULT 0,
            created_at        DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

    for zone_key, display_name, description, width, height in ZONES:
        cur.execute(
            "INSERT OR IGNORE INTO ad_zones (zone_key, display_name, description, width, height) VALUES (?,?,?,?,?)",
            (zone_key, display_name, description, width, height)
        )

    con.commit()
    con.close()
    print("migrate15 OK — advertisers, ad_zones, banner_ads creadas; 3 zonas sembradas.")

if __name__ == "__main__":
    run()

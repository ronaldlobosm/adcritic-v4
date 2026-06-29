"""
migrate6.py — Comment moderation & banned words
------------------------------------------------
- Adds column `status` to `post_comments`
- Creates table `banned_words`
- Seeds initial banned word list
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "adcritic.db")

BANNED_WORDS = [
    # Spanish
    ("pendejo","es"),("pendeja","es"),("pendejos","es"),("pendejas","es"),
    ("puta","es"),("puto","es"),("putas","es"),("putos","es"),
    ("chingada","es"),("chinga","es"),("chingado","es"),("chinguen","es"),
    ("mierda","es"),("mierdas","es"),
    ("idiota","es"),("idiotas","es"),
    ("imbecil","es"),("imbécil","es"),
    ("cabron","es"),("cabrón","es"),("cabrones","es"),
    ("joder","es"),
    ("cono","es"),("coño","es"),
    ("verga","es"),("vergas","es"),
    ("mamada","es"),("mamadas","es"),
    ("pinche","es"),("pinches","es"),
    ("gilipollas","es"),
    ("follar","es"),
    ("maricon","es"),("maricón","es"),
    ("zorra","es"),("zorras","es"),
    ("bastardo","es"),("bastardos","es"),("bastarda","es"),
    ("capullo","es"),
    ("hostia","es"),
    # English
    ("fuck","en"),("fucker","en"),("fucking","en"),("fucked","en"),
    ("shit","en"),("shitty","en"),("bullshit","en"),
    ("asshole","en"),("assholes","en"),
    ("bitch","en"),("bitches","en"),
    ("cunt","en"),("cunts","en"),
    ("dick","en"),("dicks","en"),
    ("bastard","en"),("bastards","en"),
    ("prick","en"),("pricks","en"),
    ("cock","en"),("cocks","en"),
    ("whore","en"),("whores","en"),
    ("motherfucker","en"),
    ("jackass","en"),
    ("asshat","en"),
]


def run():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 1. Add status column to post_comments (ignore if already exists)
    try:
        cur.execute(
            "ALTER TABLE post_comments ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'approved'"
        )
        print("  [+] Added column post_comments.status")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("  [=] Column post_comments.status already exists — skipping")
        else:
            raise

    # 2. Create banned_words table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS banned_words (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            word       VARCHAR(100) NOT NULL UNIQUE,
            language   VARCHAR(10)  NOT NULL DEFAULT 'all',
            created_at DATETIME     DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("  [+] Table banned_words ensured")

    # 3. Seed banned words
    inserted = 0
    for word, lang in BANNED_WORDS:
        cur.execute(
            "INSERT OR IGNORE INTO banned_words (word, language) VALUES (?, ?)",
            (word, lang),
        )
        if cur.rowcount:
            inserted += 1

    conn.commit()
    conn.close()
    print(f"  [+] Seeded {inserted} new banned words ({len(BANNED_WORDS)} total attempted)")
    print("Migration 6 complete.")


if __name__ == "__main__":
    run()

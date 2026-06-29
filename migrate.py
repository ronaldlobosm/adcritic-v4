"""
One-time migration:
  1. Create categories + ad_categories tables.
  2. Read existing ads.category text values, create Category records, link them.
  3. Convert ads.country text values to ISO-3166-1 alpha-2 codes.

Safe to run multiple times (idempotent).
"""
from app import create_app, db
from app.models import Ad, Category

# Map legacy country text → ISO code
COUNTRY_TEXT_TO_CODE = {
    "Perú":    "PE",
    "EE.UU.": "US",
    "Peru":    "PE",
    "USA":     "US",
    "US":      "US",
    "PE":      "PE",
}

# Map legacy category text → (name_es, name_en)
CATEGORY_TEXT_TO_BILINGUAL = {
    "Entretenimiento": ("Entretenimiento", "Entertainment"),
    "Moda":            ("Moda",            "Fashion"),
    "Bebidas":         ("Bebidas",         "Beverages"),
    "Tecnología":      ("Tecnología",      "Technology"),
    # extend here if your DB has others
}


def migrate():
    app = create_app()
    with app.app_context():
        # 1. Create new tables without touching existing ones
        db.create_all()
        print("db.create_all() — new tables created if missing")

        # 2. Read old category values directly via raw SQL (column may not be
        #    in the SQLAlchemy model anymore but still exists in the DB)
        with db.engine.connect() as conn:
            rows = conn.execute(
                db.text("SELECT id, category, country FROM ads")
            ).fetchall()

        for ad_id, raw_category, raw_country in rows:
            ad = Ad.query.get(ad_id)
            if ad is None:
                continue

            # --- Country migration ---
            code = COUNTRY_TEXT_TO_CODE.get(raw_country, raw_country)
            if ad.country != code:
                ad.country = code
                print(f"  ad {ad_id}: country '{raw_country}' → '{code}'")

            # --- Category migration ---
            if raw_category and not ad.categories:
                bilingual = CATEGORY_TEXT_TO_BILINGUAL.get(raw_category)
                if bilingual:
                    name_es, name_en = bilingual
                else:
                    # Unknown category: use same text for both languages
                    name_es = name_en = raw_category
                    print(f"  warning: unknown category text '{raw_category}' — using as-is")

                cat = Category.query.filter_by(name_es=name_es).first()
                if cat is None:
                    cat = Category(name_es=name_es, name_en=name_en)
                    db.session.add(cat)
                    db.session.flush()
                    print(f"  created category: {name_es} / {name_en}")

                ad.categories.append(cat)
                print(f"  ad {ad_id} ({ad.slug}): linked to category '{name_es}'")

        db.session.commit()
        print("Migration complete.")


if __name__ == "__main__":
    migrate()

"""
Run once after deploy to populate news posts from news_seed_data.json.
Safe to re-run: skips slugs that already exist.
"""
import json, os, sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from app import create_app, db
from app.models import Post, PostTranslation, PostCategory

app = create_app()

DATA_FILE = os.path.join(os.path.dirname(__file__), "news_seed_data.json")

with open(DATA_FILE) as f:
    data = json.load(f)

with app.app_context():
    # Build category id map (local id → DB category by name)
    local_cats = {r["post_id"]: r["post_category_id"] for r in data["post_cats"]}
    db_cats = {c.id: c for c in PostCategory.query.all()}

    inserted = 0
    skipped = 0

    for row in data["posts"]:
        if Post.query.filter_by(slug=row["slug"]).first():
            skipped += 1
            continue

        def parse_dt(s):
            if not s:
                return None
            for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                try:
                    return datetime.strptime(s, fmt)
                except ValueError:
                    pass
            return None

        post = Post(
            slug=row["slug"],
            author_id=row["author_id"],
            cover_image_url=row.get("cover_image_url"),
            status=row["status"],
            published_at=parse_dt(row.get("published_at")),
            is_premium=bool(row.get("is_premium", 0)),
        )
        db.session.add(post)
        db.session.flush()

        # Attach category
        cat_id = local_cats.get(row["id"])
        if cat_id and cat_id in db_cats:
            post.categories.append(db_cats[cat_id])

        # Translations
        post_translations = [t for t in data["translations"] if t["post_id"] == row["id"]]
        for t in post_translations:
            db.session.add(PostTranslation(
                post_id=post.id,
                language=t["language"],
                title=t.get("title", ""),
                excerpt=t.get("excerpt", ""),
                body=t.get("body", ""),
            ))

        inserted += 1

    db.session.commit()
    print(f"Done. Inserted: {inserted}, Skipped (already exist): {skipped}")

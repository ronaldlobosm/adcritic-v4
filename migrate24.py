"""migrate24 - Critiques-as-articles: users.username_slug, ad_comments
title/slug/reads_count, and new tables (follows, saved_critiques,
ad_debate_comments)."""

from sqlalchemy import inspect, text
from app import create_app, db
from app.models import User, AdComment  # noqa: F401 (ensures new models are registered)


def slugify(text_value):
    import re
    value = (text_value or "").strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "user"


app = create_app("default")

with app.app_context():
    # New tables (follows, saved_critiques, ad_debate_comments) are created
    # automatically by create_all() — it never touches existing tables.
    db.create_all()

    user_cols = [col["name"] for col in inspect(db.engine).get_columns("users")]
    if "username_slug" in user_cols:
        print("users.username_slug already exists")
    else:
        with db.engine.begin() as conn:
            # Note: SQLite can't add a UNIQUE column via ALTER TABLE ADD COLUMN,
            # so the column and its uniqueness are done as two steps (works
            # identically on Postgres).
            conn.execute(text("ALTER TABLE users ADD COLUMN username_slug VARCHAR(140)"))
            conn.execute(text("CREATE UNIQUE INDEX uq_users_username_slug ON users (username_slug)"))
        print("Added users.username_slug")

    comment_cols = [col["name"] for col in inspect(db.engine).get_columns("ad_comments")]
    with db.engine.begin() as conn:
        if "title" not in comment_cols:
            conn.execute(text("ALTER TABLE ad_comments ADD COLUMN title VARCHAR(200)"))
            print("Added ad_comments.title")
        if "slug" not in comment_cols:
            conn.execute(text("ALTER TABLE ad_comments ADD COLUMN slug VARCHAR(220)"))
            conn.execute(text("CREATE UNIQUE INDEX uq_ad_comments_slug ON ad_comments (slug)"))
            print("Added ad_comments.slug")
        if "reads_count" not in comment_cols:
            conn.execute(text("ALTER TABLE ad_comments ADD COLUMN reads_count INTEGER NOT NULL DEFAULT 0"))
            print("Added ad_comments.reads_count")

    # ── Backfill ──────────────────────────────────────────────────────
    # username_slug for existing users
    used_slugs = set()
    for user in User.query.filter(User.username_slug.is_(None)).all():
        base = slugify(user.display_name or user.email.split("@")[0])
        candidate = base
        i = 2
        while candidate in used_slugs or User.query.filter_by(username_slug=candidate).first():
            candidate = f"{base}-{i}"
            i += 1
        user.username_slug = candidate
        used_slugs.add(candidate)
        print(f"Backfilled username_slug for user {user.id}: {candidate}")

    # title/slug for existing critiques (AdComment rows) missing them
    used_critique_slugs = set()
    for critique in AdComment.query.filter(AdComment.slug.is_(None)).all():
        words = (critique.body or "").split()
        title = " ".join(words[:8]) or f"Critique #{critique.id}"
        base = slugify(title)
        candidate = base
        i = 2
        while candidate in used_critique_slugs or AdComment.query.filter_by(slug=candidate).first():
            candidate = f"{base}-{i}"
            i += 1
        critique.title = title
        critique.slug = candidate
        used_critique_slugs.add(candidate)
        print(f"Backfilled title/slug for critique {critique.id}: {candidate}")

    db.session.commit()
    print("migrate24 done")

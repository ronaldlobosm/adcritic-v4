"""migrate26 - Critiques are editable at any time by their author (the
5-minute window now only gates self-deletion). Adds ad_comments.updated_at
so the published page can show both "Created" and "Edited" dates."""

from sqlalchemy import inspect, text
from app import create_app, db

app = create_app("default")

with app.app_context():
    cols = [col["name"] for col in inspect(db.engine).get_columns("ad_comments")]

    if "updated_at" in cols:
        print("ad_comments.updated_at already exists")
    else:
        with db.engine.begin() as conn:
            conn.execute(text("ALTER TABLE ad_comments ADD COLUMN updated_at TIMESTAMP"))
            conn.execute(text("UPDATE ad_comments SET updated_at = created_at"))
        print("Added ad_comments.updated_at and backfilled from created_at")

    print("migrate26 done")

"""migrate27 - Admin-only cover image for Gold critiques: ads.critique_cover_image_url.
When set, it replaces the ad's own video as the featured header on every
Gold critique of that ad."""

from sqlalchemy import inspect, text
from app import create_app, db

app = create_app("default")

with app.app_context():
    cols = [col["name"] for col in inspect(db.engine).get_columns("ads")]

    if "critique_cover_image_url" in cols:
        print("ads.critique_cover_image_url already exists")
    else:
        with db.engine.begin() as conn:
            conn.execute(text(
                "ALTER TABLE ads ADD COLUMN critique_cover_image_url VARCHAR(500)"
            ))
        print("Added ads.critique_cover_image_url")

    print("migrate27 done")

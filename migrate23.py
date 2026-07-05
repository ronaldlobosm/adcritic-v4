"""migrate23 - Add other_languages to users."""

from sqlalchemy import inspect, text
from app import create_app, db


app = create_app("default")

with app.app_context():
    cols = [col["name"] for col in inspect(db.engine).get_columns("users")]
    if "other_languages" in cols:
        print("users.other_languages already exists")
    else:
        with db.engine.begin() as conn:
            conn.execute(text("ALTER TABLE users ADD COLUMN other_languages VARCHAR(200)"))
        print("Added users.other_languages")

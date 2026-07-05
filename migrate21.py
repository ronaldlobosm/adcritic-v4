"""migrate21 - Add location to users."""

from sqlalchemy import inspect, text
from app import create_app, db


app = create_app("default")

with app.app_context():
    cols = [col["name"] for col in inspect(db.engine).get_columns("users")]
    if "location" in cols:
        print("users.location already exists")
    else:
        with db.engine.begin() as conn:
            conn.execute(text("ALTER TABLE users ADD COLUMN location VARCHAR(120)"))
        print("Added users.location")

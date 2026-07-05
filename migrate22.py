"""migrate22 - Add preferred_language to users."""

from sqlalchemy import inspect, text
from app import create_app, db


app = create_app("default")

with app.app_context():
    cols = [col["name"] for col in inspect(db.engine).get_columns("users")]
    if "preferred_language" in cols:
        print("users.preferred_language already exists")
    else:
        with db.engine.begin() as conn:
            conn.execute(text("ALTER TABLE users ADD COLUMN preferred_language VARCHAR(2)"))
        print("Added users.preferred_language")

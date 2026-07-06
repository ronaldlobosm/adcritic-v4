"""migrate25 - Gold intro critique allowance goes from 1 (boolean) to 3
(counter): users.gold_intro_critiques_used replaces gold_intro_critique_used."""

from sqlalchemy import inspect, text
from app import create_app, db
from app.models import User

app = create_app("default")

with app.app_context():
    cols = [col["name"] for col in inspect(db.engine).get_columns("users")]

    if "gold_intro_critiques_used" in cols:
        print("users.gold_intro_critiques_used already exists")
    else:
        with db.engine.begin() as conn:
            conn.execute(text(
                "ALTER TABLE users ADD COLUMN gold_intro_critiques_used INTEGER NOT NULL DEFAULT 0"
            ))
        print("Added users.gold_intro_critiques_used")

        if "gold_intro_critique_used" in cols:
            with db.engine.begin() as conn:
                conn.execute(text(
                    "UPDATE users SET gold_intro_critiques_used = 3 WHERE gold_intro_critique_used = 1"
                ))
            print("Backfilled gold_intro_critiques_used from legacy gold_intro_critique_used")

    print("migrate25 done")

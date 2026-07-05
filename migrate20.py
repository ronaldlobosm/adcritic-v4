"""migrate20 — Add linkedin_url to users."""
from app import create_app, db
from sqlalchemy import inspect, text


def migrate():
    app = create_app()
    with app.app_context():
        db.create_all()
        cols = [col["name"] for col in inspect(db.engine).get_columns("users")]
        if "linkedin_url" in cols:
            print("users.linkedin_url already exists")
            return

        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE users ADD COLUMN linkedin_url VARCHAR(300)"))
            conn.commit()
        print("Added users.linkedin_url")


if __name__ == "__main__":
    migrate()

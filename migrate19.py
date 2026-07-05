"""migrate19 — Add critique likes, critique ratings and saved ads."""
from app import create_app, db
from app.models import AdCommentLike, AdCommentRating, SavedAd


def migrate():
    app = create_app()
    with app.app_context():
        db.create_all()
        print("Created interaction tables if missing:")
        print(f"  - {AdCommentLike.__tablename__}")
        print(f"  - {AdCommentRating.__tablename__}")
        print(f"  - {SavedAd.__tablename__}")


if __name__ == "__main__":
    migrate()

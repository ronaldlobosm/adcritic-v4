import os
from dotenv import load_dotenv

load_dotenv(override=True)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_BASE = os.path.join(BASE_DIR, "app", "static", "uploads")


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-in-prod")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024 * 1024  # 2 GB (raw video before transcoding)
    UPLOAD_FOLDER = UPLOAD_BASE
    # Flask-Mail
    MAIL_SERVER          = os.environ.get("MAIL_SERVER",   "smtp.gmail.com")
    MAIL_PORT            = int(os.environ.get("MAIL_PORT", "587"))
    MAIL_USE_TLS         = os.environ.get("MAIL_USE_TLS",  "true").lower() == "true"
    MAIL_USERNAME        = os.environ.get("MAIL_USERNAME", "")
    MAIL_PASSWORD        = os.environ.get("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER  = os.environ.get("MAIL_FROM",     "AdCritic <noreply@adcritic.com>")
    SITE_URL             = os.environ.get("SITE_URL",      "http://localhost:5000")


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(BASE_DIR, 'adcritic.db')}",
    )


class ProductionConfig(Config):
    DEBUG = False
    # Render sets DATABASE_URL with postgres:// — SQLAlchemy needs postgresql://
    _db_url = os.environ.get("DATABASE_URL", "")
    # Normalize URL and use psycopg3 dialect (compatible with Python 3.14)
    _db_url = _db_url.replace("postgres://", "postgresql://", 1)
    _db_url = _db_url.replace("postgresql://", "postgresql+psycopg://", 1)
    SQLALCHEMY_DATABASE_URI = _db_url if _db_url else None


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}

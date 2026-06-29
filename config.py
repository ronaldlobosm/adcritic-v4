import os
from dotenv import load_dotenv

load_dotenv(override=True)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_BASE = os.path.join(BASE_DIR, "app", "static", "uploads")


def _build_db_url():
    url = os.environ.get("DATABASE_URL", "")
    url = url.replace("postgres://", "postgresql://", 1)
    url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url or None


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
    SQLALCHEMY_DATABASE_URI = (
        _build_db_url()
        or f"sqlite:///{os.path.join(BASE_DIR, 'adcritic.db')}"
    )


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = _build_db_url()


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}

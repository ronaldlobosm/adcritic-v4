import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()


def _ensure_runtime_schema():
    """Keep deployed databases compatible when profile features are introduced."""
    from sqlalchemy import inspect, text

    inspector = inspect(db.engine)
    existing_tables = set(inspector.get_table_names())

    runtime_tables = [
        "ad_comment_likes",
        "ad_comment_ratings",
        "saved_ads",
    ]
    missing_tables = [
        db.metadata.tables[name]
        for name in runtime_tables
        if name in db.metadata.tables and name not in existing_tables
    ]
    if missing_tables:
        db.metadata.create_all(bind=db.engine, tables=missing_tables)

    if not inspector.has_table("users"):
        return

    existing = {col["name"] for col in inspector.get_columns("users")}
    required = [
        ("linkedin_url", "ALTER TABLE users ADD COLUMN linkedin_url VARCHAR(300)"),
        ("location", "ALTER TABLE users ADD COLUMN location VARCHAR(120)"),
    ]
    with db.engine.begin() as conn:
        for col, ddl in required:
            if col not in existing:
                conn.execute(text(ddl))


def create_app(config_name=None):
    app = Flask(__name__)

    from config import config
    cfg_name = config_name or os.environ.get("FLASK_ENV", "default")
    app.config.from_object(config[cfg_name])

    db.init_app(app)
    mail.init_app(app)

    with app.app_context():
        _ensure_runtime_schema()

    login_manager.init_app(app)
    login_manager.login_view = "auth.login_es"
    login_manager.login_message = "Debes iniciar sesión para acceder a esa página."
    login_manager.login_message_category = "info"

    from app.models import User, Category, PostCategory, MediaFile
    from app.permissions import has_content_access

    @login_manager.user_loader
    def load_user(user_id):
        user = User.query.get(int(user_id))
        if user is None or not user.is_active:
            return None
        return user

    @app.context_processor
    def inject_nav_data():
        from datetime import datetime as _dt

        def relative_date(dt, lang="es"):
            if dt is None:
                return ""
            diff = _dt.utcnow() - dt
            d = diff.days
            s = diff.seconds
            if d == 0:
                h = s // 3600
                if h == 0:
                    m = s // 60
                    if lang == "es":
                        return f"hace {m} min" if m > 1 else "ahora"
                    return f"{m} min ago" if m > 1 else "just now"
                if lang == "es":
                    return f"hace {h} h"
                return f"{h}h ago"
            if d == 1:
                return "ayer" if lang == "es" else "yesterday"
            if d < 7:
                return (f"hace {d} días" if lang == "es" else f"{d} days ago")
            if d < 30:
                w = d // 7
                return (f"hace {w} semana{'s' if w>1 else ''}" if lang == "es"
                        else f"{w} week{'s' if w>1 else ''} ago")
            if d < 365:
                mo = d // 30
                return (f"hace {mo} mes{'es' if mo>1 else ''}" if lang == "es"
                        else f"{mo} month{'s' if mo>1 else ''} ago")
            y = d // 365
            return (f"hace {y} año{'s' if y>1 else ''}" if lang == "es"
                    else f"{y} year{'s' if y>1 else ''} ago")

        def format_date(dt, lang="es", compact=False):
            if dt is None:
                return ""
            months = {
                "es": [
                    "enero", "febrero", "marzo", "abril", "mayo", "junio",
                    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
                ],
                "en": [
                    "January", "February", "March", "April", "May", "June",
                    "July", "August", "September", "October", "November", "December",
                ],
            }
            short = {
                "es": ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"],
                "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
            }
            names = short[lang] if compact else months[lang]
            month = names[dt.month - 1]
            if compact:
                return f"{dt.day:02d} {month} {dt.year}" if lang == "es" else f"{month} {dt.day}, {dt.year}"
            return f"{dt.day} de {month} de {dt.year}" if lang == "es" else f"{month} {dt.day}, {dt.year}"

        def user_can(content_type):
            """Template helper: does current_user have access to this content section?"""
            from flask_login import current_user as _cu
            return has_content_access(_cu, content_type)

        def media_alt(url, lang="es"):
            """Return alt text for a media URL, looked up from MediaFile."""
            if not url:
                return ""
            try:
                filename = url.rsplit("/", 1)[-1]
                mf = MediaFile.query.filter_by(filename=filename).first()
                if mf:
                    return mf.display_alt(lang)
            except Exception:
                pass
            return ""

        try:
            return {
                "nav_ad_categories":   Category.query.order_by(Category.name_es).all(),
                "nav_post_categories": PostCategory.query.order_by(PostCategory.name_es).all(),
                "relative_date":       relative_date,
                "format_date":         format_date,
                "media_alt":           media_alt,
                "user_can":            user_can,
            }
        except Exception:
            return {
                "nav_ad_categories":  [], "nav_post_categories": [],
                "relative_date":      relative_date,
                "format_date":        format_date,
                "media_alt":          lambda url, lang="es": "",
                "user_can":           lambda ct: False,
            }

    from app.routes.main       import main          as main_bp
    from app.routes.auth       import auth          as auth_bp
    from app.routes.admin      import admin         as admin_bp
    from app.routes.account    import account       as account_bp
    from app.routes.posts      import posts_bp
    from app.routes.media      import media_bp
    from app.routes.membership import membership_bp
    from app.routes.advertising import advertising_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(account_bp)
    app.register_blueprint(posts_bp)
    app.register_blueprint(media_bp)
    app.register_blueprint(membership_bp)
    app.register_blueprint(advertising_bp)

    # ── Jinja2 global: get_ad_zone(zone_key) ──────────────────────────
    import random as _random
    from datetime import date as _date

    def get_ad_zone(zone_key):
        """Return a random active BannerAd for zone_key, increment impressions.
        Returns None if no active ad exists (template renders nothing)."""
        try:
            from app.models import BannerAd, AdZone
            import sqlalchemy as _sa
            zone = AdZone.query.filter_by(zone_key=zone_key).first()
            if not zone:
                return None
            today = _date.today()
            candidates = (
                BannerAd.query
                .filter_by(zone_id=zone.id, is_active=True)
                .filter(
                    _sa.or_(BannerAd.start_date.is_(None), BannerAd.start_date <= today),
                    _sa.or_(BannerAd.end_date.is_(None),   BannerAd.end_date   >= today),
                )
                .all()
            )
            if not candidates:
                return None
            ad = _random.choice(candidates)
            ad.impressions_count = (ad.impressions_count or 0) + 1
            db.session.commit()
            return ad
        except Exception:
            return None

    app.jinja_env.globals["get_ad_zone"] = get_ad_zone

    return app

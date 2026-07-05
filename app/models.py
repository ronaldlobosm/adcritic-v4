from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


# ============================================================
# Catalog: Ad + categories (M2M)
# ============================================================

ad_categories = db.Table(
    "ad_categories",
    db.Column("ad_id",       db.Integer, db.ForeignKey("ads.id"),        primary_key=True),
    db.Column("category_id", db.Integer, db.ForeignKey("categories.id"), primary_key=True),
)


class Category(db.Model):
    __tablename__ = "categories"

    id      = db.Column(db.Integer, primary_key=True)
    name_es = db.Column(db.String(100), nullable=False, unique=True)
    name_en = db.Column(db.String(100), nullable=False, unique=True)

    def name(self, lang):
        return self.name_es if lang == "es" else self.name_en

    def __repr__(self):
        return f"<Category {self.name_es}>"


class Ad(db.Model):
    __tablename__ = "ads"

    id                 = db.Column(db.Integer, primary_key=True)
    slug               = db.Column(db.String(120), unique=True, nullable=False, index=True)
    brand              = db.Column(db.String(120), nullable=False, index=True)
    country            = db.Column(db.String(10),  nullable=False, index=True)
    year               = db.Column(db.Integer,     nullable=False, index=True)
    youtube_id         = db.Column(db.String(20),  nullable=False)  # legacy; keep for NOT NULL constraint
    video_source_type  = db.Column(db.String(20),  nullable=True)   # 'youtube','vimeo','upload'
    video_source_value = db.Column(db.String(500), nullable=True)
    subtitle_es        = db.Column(db.String(300), nullable=True)   # stored filename
    subtitle_en        = db.Column(db.String(300), nullable=True)
    is_premium         = db.Column(db.Boolean, nullable=False, default=False)
    is_featured        = db.Column(db.Boolean, nullable=False, default=False)
    # Workflow
    status             = db.Column(db.String(20), nullable=False, default="published")
    # valid: 'draft' | 'pending' | 'published' | 'rejected'
    published_at       = db.Column(db.DateTime, nullable=True)
    rejection_note     = db.Column(db.Text, nullable=True)
    created_by_id      = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at         = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def video_type(self):
        return self.video_source_type or ("youtube" if self.youtube_id else None)

    @property
    def video_value(self):
        return self.video_source_value or self.youtube_id or None

    creator = db.relationship("User", foreign_keys=[created_by_id])
    translations = db.relationship(
        "AdTranslation", backref="ad", lazy="dynamic", cascade="all, delete-orphan"
    )
    categories = db.relationship(
        "Category", secondary=ad_categories, backref="ads", lazy="subquery"
    )
    comments = db.relationship(
        "AdComment", backref="ad", lazy="dynamic",
        cascade="all, delete-orphan",
        order_by="AdComment.created_at.desc()",
    )

    def translation(self, lang):
        return self.translations.filter_by(language=lang).first()

    def __repr__(self):
        return f"<Ad {self.slug}>"


class AdTranslation(db.Model):
    __tablename__ = "ad_translations"

    id               = db.Column(db.Integer, primary_key=True)
    ad_id            = db.Column(db.Integer, db.ForeignKey("ads.id"), nullable=False)
    language         = db.Column(db.String(5), nullable=False)
    title            = db.Column(db.String(200), nullable=False)
    analysis_text    = db.Column(db.Text, nullable=False)
    meta_title       = db.Column(db.String(200), nullable=True)
    meta_description = db.Column(db.String(300), nullable=True)

    __table_args__ = (
        db.UniqueConstraint("ad_id", "language", name="uq_ad_language"),
    )


# ============================================================
# News / Posts
# ============================================================

post_post_categories = db.Table(
    "post_post_categories",
    db.Column("post_id",          db.Integer, db.ForeignKey("posts.id"),          primary_key=True),
    db.Column("post_category_id", db.Integer, db.ForeignKey("post_categories.id"), primary_key=True),
)


class PostCategory(db.Model):
    __tablename__ = "post_categories"

    id      = db.Column(db.Integer, primary_key=True)
    name_es = db.Column(db.String(100), nullable=False, unique=True)
    name_en = db.Column(db.String(100), nullable=False, unique=True)

    def name(self, lang):
        return self.name_es if lang == "es" else self.name_en

    def __repr__(self):
        return f"<PostCategory {self.name_es}>"


class Post(db.Model):
    __tablename__ = "posts"

    id                 = db.Column(db.Integer, primary_key=True)
    slug               = db.Column(db.String(160), unique=True, nullable=False, index=True)
    author_id          = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    cover_image_url    = db.Column(db.String(500), nullable=True)
    youtube_id         = db.Column(db.String(20), nullable=True)  # legacy
    video_source_type  = db.Column(db.String(20), nullable=True)
    video_source_value = db.Column(db.String(500), nullable=True)
    subtitle_es        = db.Column(db.String(300), nullable=True)
    subtitle_en        = db.Column(db.String(300), nullable=True)
    is_premium         = db.Column(db.Boolean, nullable=False, default=False)
    published_at       = db.Column(db.DateTime, nullable=True, index=True)
    # Workflow
    status             = db.Column(db.String(20), nullable=False, default="published")
    # valid: 'draft' | 'pending' | 'published' | 'rejected'
    rejection_note     = db.Column(db.Text, nullable=True)
    views_count        = db.Column(db.Integer, nullable=False, default=0)
    created_at         = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def video_type(self):
        return self.video_source_type or ("youtube" if self.youtube_id else None)

    @property
    def video_value(self):
        return self.video_source_value or self.youtube_id or None

    author = db.relationship("User", backref="authored_posts")
    translations = db.relationship(
        "PostTranslation", backref="post", lazy="dynamic", cascade="all, delete-orphan"
    )
    categories = db.relationship(
        "PostCategory", secondary=post_post_categories, backref="posts", lazy="subquery"
    )
    comments = db.relationship(
        "PostComment", backref="post", lazy="dynamic",
        cascade="all, delete-orphan",
        order_by="PostComment.created_at.desc()",
    )

    def translation(self, lang):
        return self.translations.filter_by(language=lang).first()

    @property
    def is_published(self):
        return (
            self.status == "published"
            and self.published_at is not None
            and self.published_at <= datetime.utcnow()
        )

    def __repr__(self):
        return f"<Post {self.slug}>"


class PostTranslation(db.Model):
    __tablename__ = "post_translations"

    id               = db.Column(db.Integer, primary_key=True)
    post_id          = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False)
    language         = db.Column(db.String(5), nullable=False)
    title            = db.Column(db.String(250), nullable=False)
    excerpt          = db.Column(db.Text, nullable=False)
    body             = db.Column(db.Text, nullable=False)
    meta_title       = db.Column(db.String(250), nullable=True)
    meta_description = db.Column(db.String(300), nullable=True)

    __table_args__ = (
        db.UniqueConstraint("post_id", "language", name="uq_post_language"),
    )


class PostComment(db.Model):
    __tablename__ = "post_comments"

    id         = db.Column(db.Integer, primary_key=True)
    post_id    = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False)
    user_id    = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    body       = db.Column(db.Text, nullable=False)
    status     = db.Column(db.String(20), nullable=False, default="approved")
    # valid: 'approved' | 'pending' | 'spam'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User")

    def __repr__(self):
        return f"<PostComment post={self.post_id} user={self.user_id}>"


class AdComment(db.Model):
    __tablename__ = "ad_comments"

    id         = db.Column(db.Integer, primary_key=True)
    ad_id      = db.Column(db.Integer, db.ForeignKey("ads.id"), nullable=False)
    user_id    = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    body       = db.Column(db.Text, nullable=False)
    body_language       = db.Column(db.String(5), nullable=False, default="es")
    translated_body     = db.Column(db.Text, nullable=True)
    translated_language = db.Column(db.String(5), nullable=True)
    translation_provider = db.Column(db.String(80), nullable=True)
    rating_music         = db.Column(db.Integer, nullable=True)
    rating_art_direction = db.Column(db.Integer, nullable=True)
    rating_copywriting   = db.Column(db.Integer, nullable=True)
    rating_strategy      = db.Column(db.Integer, nullable=True)
    status     = db.Column(db.String(20), nullable=False, default="approved")
    # valid: 'approved' | 'pending' | 'spam'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User")

    def body_for(self, lang):
        if self.translated_body and self.translated_language == lang and self.body_language != lang:
            return self.translated_body
        return self.body

    def is_translated_for(self, lang):
        return bool(
            self.translated_body
            and self.translated_language == lang
            and self.body_language != lang
        )

    def __repr__(self):
        return f"<AdComment ad={self.ad_id} user={self.user_id}>"


class AdCommentLike(db.Model):
    __tablename__ = "ad_comment_likes"
    __table_args__ = (
        db.UniqueConstraint("comment_id", "user_id", name="uq_ad_comment_like_user"),
    )

    id         = db.Column(db.Integer, primary_key=True)
    comment_id = db.Column(db.Integer, db.ForeignKey("ad_comments.id"), nullable=False, index=True)
    user_id    = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    comment = db.relationship("AdComment", backref=db.backref("likes", lazy="dynamic", cascade="all, delete-orphan"))
    user    = db.relationship("User")


class AdCommentRating(db.Model):
    __tablename__ = "ad_comment_ratings"
    __table_args__ = (
        db.UniqueConstraint("comment_id", "user_id", name="uq_ad_comment_rating_user"),
    )

    id         = db.Column(db.Integer, primary_key=True)
    comment_id = db.Column(db.Integer, db.ForeignKey("ad_comments.id"), nullable=False, index=True)
    user_id    = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    rating     = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    comment = db.relationship("AdComment", backref=db.backref("community_ratings", lazy="dynamic", cascade="all, delete-orphan"))
    user    = db.relationship("User")


class SavedAd(db.Model):
    __tablename__ = "saved_ads"
    __table_args__ = (
        db.UniqueConstraint("ad_id", "user_id", name="uq_saved_ad_user"),
    )

    id         = db.Column(db.Integer, primary_key=True)
    ad_id      = db.Column(db.Integer, db.ForeignKey("ads.id"), nullable=False, index=True)
    user_id    = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    ad   = db.relationship("Ad", backref=db.backref("saves", lazy="dynamic", cascade="all, delete-orphan"))
    user = db.relationship("User")


class BannedWord(db.Model):
    __tablename__ = "banned_words"

    id         = db.Column(db.Integer, primary_key=True)
    word       = db.Column(db.String(100), nullable=False, unique=True)
    language   = db.Column(db.String(10), nullable=False, default="all")
    # 'es' | 'en' | 'all'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<BannedWord {self.word}>"


# ============================================================
# User
# ============================================================

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id            = db.Column(db.Integer, primary_key=True)
    email         = db.Column(db.String(200), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role          = db.Column(db.String(20), nullable=False, default="free")
    is_active     = db.Column(db.Boolean, nullable=False, default=True)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    # Public profile
    display_name    = db.Column(db.String(100), nullable=True)
    professional_title = db.Column(db.String(140), nullable=True)
    avatar_media_id = db.Column(db.Integer, db.ForeignKey("media_files.id"), nullable=True)
    bio_es          = db.Column(db.Text, nullable=True)
    bio_en          = db.Column(db.Text, nullable=True)
    linkedin_url    = db.Column(db.String(300), nullable=True)

    # Email verification
    email_verified         = db.Column(db.Boolean, nullable=False, default=False)
    email_verify_token     = db.Column(db.String(100), nullable=True, unique=True)
    email_verify_code      = db.Column(db.String(6),   nullable=True)
    email_verify_sent_at   = db.Column(db.DateTime,    nullable=True)
    password_reset_token   = db.Column(db.String(100), nullable=True, unique=True)
    password_reset_sent_at = db.Column(db.DateTime,    nullable=True)

    # Stripe subscription
    stripe_customer_id     = db.Column(db.String(100), nullable=True, unique=True)
    stripe_subscription_id = db.Column(db.String(100), nullable=True, unique=True)
    stripe_price_id        = db.Column(db.String(100), nullable=True)
    gold_started_at        = db.Column(db.DateTime, nullable=True)
    gold_intro_critique_used = db.Column(db.Boolean, nullable=False, default=False)

    # Valid roles: admin · approver · editor · advertiser · gold · free
    ROLES = ("admin", "approver", "editor", "advertiser", "gold", "free")

    # Relationships
    avatar = db.relationship("MediaFile", foreign_keys=[avatar_media_id])
    content_access = db.relationship(
        "RoleContentAccess",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_staff(self):
        """True for any role that can access the admin panel."""
        return self.role in ("admin", "approver", "editor", "advertiser")

    @property
    def public_name(self):
        """Display name shown publicly (falls back to email prefix)."""
        return self.display_name or self.email.split("@")[0]

    @property
    def avatar_url(self):
        if self.avatar and self.avatar.thumbnail_url:
            return self.avatar.thumbnail_url
        return None

    def __repr__(self):
        return f"<User {self.email} [{self.role}]>"


class RoleContentAccess(db.Model):
    """
    Grants an editor or approver access to a specific content type.
    content_type: 'catalog' or 'posts'
    section_id:   None → access to all sections; int → specific category ID
    """
    __tablename__ = "role_content_access"

    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content_type = db.Column(db.String(20), nullable=False)
    section_id   = db.Column(db.Integer, nullable=True)

    user = db.relationship("User", back_populates="content_access")

    __table_args__ = (
        db.UniqueConstraint("user_id", "content_type", name="uq_user_content_type"),
    )


# ============================================================
# Media files
# ============================================================

class MediaFile(db.Model):
    __tablename__ = "media_files"

    id                = db.Column(db.Integer, primary_key=True)
    filename          = db.Column(db.String(300), nullable=False)          # stored uuid-based name
    original_filename = db.Column(db.String(300), nullable=False)
    file_type         = db.Column(db.String(20),  nullable=False)          # 'image','video','subtitle'
    uploaded_by       = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    uploaded_at       = db.Column(db.DateTime, default=datetime.utcnow)
    file_size         = db.Column(db.Integer, nullable=False, default=0)   # bytes

    # Optimized thumbnail (images only — 400px wide JPEG)
    thumbnail         = db.Column(db.String(300), nullable=True)

    # Remote storage (Cloudinary when configured)
    remote_url        = db.Column(db.String(700), nullable=True)
    thumbnail_remote_url = db.Column(db.String(700), nullable=True)
    cloudinary_public_id = db.Column(db.String(300), nullable=True)
    thumbnail_cloudinary_public_id = db.Column(db.String(300), nullable=True)

    # Editable metadata
    title_es          = db.Column(db.String(300), nullable=True)
    title_en          = db.Column(db.String(300), nullable=True)
    alt_text_es       = db.Column(db.String(300), nullable=True)
    alt_text_en       = db.Column(db.String(300), nullable=True)
    description       = db.Column(db.Text, nullable=True)

    uploader = db.relationship("User", foreign_keys=[uploaded_by])

    _SUBFOLDERS = {"image": "images", "video": "videos", "subtitle": "subtitles"}

    @property
    def url(self):
        if self.remote_url:
            return self.remote_url
        subfolder = self._SUBFOLDERS.get(self.file_type, "images")
        return f"/static/uploads/{subfolder}/{self.filename}"

    @property
    def thumbnail_url(self):
        if self.thumbnail_remote_url:
            return self.thumbnail_remote_url
        if self.thumbnail:
            return f"/static/uploads/images/{self.thumbnail}"
        return self.url

    def display_title(self, lang="es"):
        if lang == "es":
            return self.title_es or self.title_en or self.original_filename
        return self.title_en or self.title_es or self.original_filename

    def display_alt(self, lang="es"):
        if lang == "es":
            return self.alt_text_es or self.alt_text_en or ""
        return self.alt_text_en or self.alt_text_es or ""

    @property
    def size_display(self):
        b = self.file_size
        if b < 1024:
            return f"{b} B"
        if b < 1024 * 1024:
            return f"{b/1024:.1f} KB"
        return f"{b/1024/1024:.1f} MB"

    def to_json(self):
        return {
            "id":          self.id,
            "url":         self.url,
            "thumbnail_url": self.thumbnail_url,
            "filename":    self.original_filename,
            "file_type":   self.file_type,
            "size":        self.size_display,
            "title_es":    self.title_es or "",
            "title_en":    self.title_en or "",
            "alt_text_es": self.alt_text_es or "",
            "alt_text_en": self.alt_text_en or "",
            "description": self.description or "",
        }

    def __repr__(self):
        return f"<MediaFile {self.filename}>"


# ============================================================
# Newsletter
# ============================================================

class NewsletterSubscriber(db.Model):
    __tablename__ = "newsletter_subscribers"

    id         = db.Column(db.Integer, primary_key=True)
    email      = db.Column(db.String(200), unique=True, nullable=False)
    language   = db.Column(db.String(5), nullable=False, default="es")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ============================================================
# Site Settings (single row)
# ============================================================

# ============================================================
# Advertising / Banner system
# ============================================================

class Advertiser(db.Model):
    __tablename__ = "advertisers"

    id            = db.Column(db.Integer, primary_key=True)
    company_name  = db.Column(db.String(200), nullable=False)
    contact_name  = db.Column(db.String(200), nullable=True)
    contact_email = db.Column(db.String(200), nullable=True)
    is_active     = db.Column(db.Boolean, nullable=False, default=True)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    campaigns = db.relationship("AdCampaign", backref="advertiser", lazy="dynamic",
                                order_by="AdCampaign.name")
    banners   = db.relationship("BannerAd", backref="advertiser", lazy="dynamic")

    def __repr__(self):
        return f"<Advertiser {self.company_name}>"


class AdCampaign(db.Model):
    __tablename__ = "ad_campaigns"

    CATEGORIES = ("awareness", "conversion", "retargeting", "launch", "seasonal", "institutional")

    id            = db.Column(db.Integer, primary_key=True)
    advertiser_id = db.Column(db.Integer, db.ForeignKey("advertisers.id"), nullable=True)
    name          = db.Column(db.String(200), nullable=False)
    category      = db.Column(db.String(40), nullable=True)   # one of CATEGORIES
    is_active     = db.Column(db.Boolean, nullable=False, default=True)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    banners = db.relationship("BannerAd", backref="campaign", lazy="dynamic")

    def __repr__(self):
        return f"<AdCampaign {self.name}>"


class AdZone(db.Model):
    __tablename__ = "ad_zones"

    id           = db.Column(db.Integer, primary_key=True)
    zone_key     = db.Column(db.String(80), unique=True, nullable=False)
    display_name = db.Column(db.String(200), nullable=False)
    description  = db.Column(db.Text, nullable=True)
    width        = db.Column(db.Integer, nullable=True)   # recommended px
    height       = db.Column(db.Integer, nullable=True)

    banners = db.relationship("BannerAd", backref="zone", lazy="dynamic")

    def __repr__(self):
        return f"<AdZone {self.zone_key}>"


class BannerAd(db.Model):
    __tablename__ = "banner_ads"

    id                = db.Column(db.Integer, primary_key=True)
    name              = db.Column(db.String(200), nullable=True)
    advertiser_id     = db.Column(db.Integer, db.ForeignKey("advertisers.id"), nullable=True)
    campaign_id       = db.Column(db.Integer, db.ForeignKey("ad_campaigns.id"), nullable=True)
    zone_id           = db.Column(db.Integer, db.ForeignKey("ad_zones.id"), nullable=False)
    ad_type           = db.Column(db.String(20), nullable=False, default="image")
    content           = db.Column(db.Text, nullable=False)
    click_url         = db.Column(db.String(500), nullable=True)
    start_date        = db.Column(db.Date, nullable=True)
    end_date          = db.Column(db.Date, nullable=True)
    # geo: comma-separated ISO-2 codes, e.g. "PE,CL" — empty means unrestricted
    target_countries  = db.Column(db.String(500), nullable=True)   # whitelist
    blocked_countries = db.Column(db.String(500), nullable=True)   # blacklist
    is_active         = db.Column(db.Boolean, nullable=False, default=True)
    impressions_count = db.Column(db.Integer, nullable=False, default=0)
    clicks_count      = db.Column(db.Integer, nullable=False, default=0)
    created_at        = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def target_list(self):
        return [c.strip().upper() for c in (self.target_countries or "").split(",") if c.strip()]

    @property
    def blocked_list(self):
        return [c.strip().upper() for c in (self.blocked_countries or "").split(",") if c.strip()]

    def __repr__(self):
        return f"<BannerAd {self.id} {self.name or ''} zone={self.zone_id}>"


class SiteSettings(db.Model):
    __tablename__ = "site_settings"

    id             = db.Column(db.Integer, primary_key=True)
    site_name      = db.Column(db.String(200), nullable=False, default="AdCritic")
    description_es = db.Column(db.Text, nullable=True)
    description_en = db.Column(db.Text, nullable=True)
    site_url       = db.Column(db.String(300), nullable=True)

    @classmethod
    def get(cls):
        obj = cls.query.first()
        if obj is None:
            obj = cls()
            from app import db as _db
            _db.session.add(obj)
            _db.session.commit()
        return obj

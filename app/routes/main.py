from datetime import datetime, timedelta
import random

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import current_user
from app import db
from app.models import Ad, AdTranslation, AdComment, Category, NewsletterSubscriber, Post, PostTranslation
from app.countries import COUNTRIES, country_name, countries_sorted
from app.utils import can_read_ad_analysis, can_comment_on_ad
from app.translation import language_name, translate_text

main = Blueprint("main", __name__)

# ---------------------------------------------------------------------------
# UI strings for ad detail (comments + paywall)
# ---------------------------------------------------------------------------

CATALOG_UI = {
    "es": {
        "comments_title":        "Críticas",
        "comment_empty":         "Sé el primero en publicar una crítica.",
        "comment_placeholder":   "Escribe tu crítica...",
        "comment_btn":           "Publicar crítica",
        "comment_ok":            "Crítica publicada.",
        "comment_updated":       "Crítica actualizada.",
        "comment_pending":       "Tu crítica está pendiente de revisión.",
        "comment_err":           "La crítica no puede estar vacía.",
        "comment_one_only":      "Ya publicaste tu crítica para este anuncio.",
        "comment_locked":        "Tu crítica ya quedó cerrada. Solo se puede editar durante los primeros 5 minutos.",
        "comment_edit_title":    "Editar tu crítica",
        "comment_locked_title":  "Crítica publicada",
        "comment_locked_body":   "Cada miembro Gold puede publicar una sola crítica por anuncio. La edición queda abierta por 5 minutos después de publicarla.",
        "comment_update_btn":    "Actualizar crítica",
        "comment_edit_window":   "Puedes editarla durante 5 minutos desde su publicación.",
        "comment_gold_since_title": "Tu membresía Gold marca el corte",
        "comment_gold_since_body":  "Puedes publicar críticas en anuncios agregados desde que eres Gold.",
        "comment_intro_title":      "Primera crítica de cortesía",
        "comment_intro_body":       "Este anuncio es anterior a tu membresía. Puedes usar aquí tu única crítica retroactiva.",
        "rating_err":            "Completa todas las valoraciones.",
        "rating_music":          "Música / sonido",
        "rating_art_direction":  "Dirección de arte",
        "rating_copywriting":    "Idea / copy",
        "rating_strategy":       "Estrategia",
        "rating_scale_hint":     "1 = flojo · 5 = brillante",
        "translated_by":         "Traducido automáticamente por {provider}",
        "view_original":         "Ver original",
        "view_translation":      "Ver traducción",
        "original_in":           "Original en {language}",
        "comment_delete_confirm":"¿Eliminar tu crítica? No se puede deshacer.",
        "comment_login":         "Inicia sesión para publicar una crítica.",
        "comment_login_link":    "Iniciar sesión",
        "gold_only_title":       "Critica como miembro Gold",
        "gold_only_body":        "Comparte tu crítica profesional sobre este anuncio con una membresía Gold.",
        "gold_only_cta":         "Ver planes de membresía",
        "gold_only_url":         "/es/membresia/",
        "by":                    "Por",
        "paywall_title":         "Análisis exclusivo para miembros Gold",
        "paywall_body":          "El análisis completo está disponible solo para suscriptores Gold.",
        "paywall_cta":           "Ver planes de membresía",
        "paywall_url":           "/es/membresia/",
        "gold_badge":            "Gold",
    },
    "en": {
        "comments_title":        "Critiques",
        "comment_empty":         "Be the first to post a critique.",
        "comment_placeholder":   "Write your critique...",
        "comment_btn":           "Post critique",
        "comment_ok":            "Critique posted.",
        "comment_updated":       "Critique updated.",
        "comment_pending":       "Your critique is pending review.",
        "comment_err":           "Critique cannot be empty.",
        "comment_one_only":      "You've already posted your critique for this ad.",
        "comment_locked":        "Your critique is locked. It can only be edited during the first 5 minutes.",
        "comment_edit_title":    "Edit your critique",
        "comment_locked_title":  "Critique published",
        "comment_locked_body":   "Each Gold member can publish one critique per ad. Editing stays open for 5 minutes after posting.",
        "comment_update_btn":    "Update critique",
        "comment_edit_window":   "You can edit it for 5 minutes after posting.",
        "comment_gold_since_title": "Your Gold membership sets the line",
        "comment_gold_since_body":  "You can publish critiques on ads added since you became Gold.",
        "comment_intro_title":      "First courtesy critique",
        "comment_intro_body":       "This ad predates your membership. You can use your single retroactive critique here.",
        "rating_err":            "Complete every rating.",
        "rating_music":          "Music / sound",
        "rating_art_direction":  "Art direction",
        "rating_copywriting":    "Idea / copy",
        "rating_strategy":       "Strategy",
        "rating_scale_hint":     "1 = weak · 5 = brilliant",
        "translated_by":         "Automatically translated by {provider}",
        "view_original":         "View original",
        "view_translation":      "View translation",
        "original_in":           "Original in {language}",
        "comment_delete_confirm":"Delete your critique? This cannot be undone.",
        "comment_login":         "Sign in to post a critique.",
        "comment_login_link":    "Sign in",
        "gold_only_title":       "Critique as a Gold member",
        "gold_only_body":        "Share your professional critique of this ad with a Gold membership.",
        "gold_only_cta":         "View membership plans",
        "gold_only_url":         "/en/membership/",
        "by":                    "By",
        "paywall_title":         "Gold member exclusive analysis",
        "paywall_body":          "The full analysis is available to Gold subscribers only.",
        "paywall_cta":           "View membership plans",
        "paywall_url":           "/en/membership/",
        "gold_badge":            "Gold",
    },
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _filtered_ads(lang):
    """Return (ads list, active filter dict) respecting query-string params."""
    from app.models import ad_categories  # avoid circular at module level

    query = (Ad.query
             .join(Ad.translations).filter(AdTranslation.language == lang)
             .filter(Ad.status == "published"))

    brand       = request.args.get("brand", "").strip()
    country     = request.args.get("country", "").strip()
    year        = request.args.get("year", "").strip()
    category_id = request.args.get("category_id", "").strip()
    columns     = request.args.get("columns", "2").strip()

    if brand:
        query = query.filter(Ad.brand.ilike(f"%{brand}%"))
    if country:
        query = query.filter(Ad.country == country)
    if year and year.isdigit():
        query = query.filter(Ad.year == int(year))
    if category_id and category_id.isdigit():
        query = query.filter(Ad.categories.any(Category.id == int(category_id)))

    ads = query.order_by(Ad.year.desc(), Ad.id.desc()).all()
    filters = {
        "brand":       brand,
        "country":     country,
        "year":        year,
        "category_id": category_id,
        "columns":     columns if columns in ("2", "3") else "2",
    }
    return ads, filters


def _filter_options(lang):
    """Values for filter dropdowns — countries limited to those in the DB."""
    used_codes = [r[0] for r in db.session.query(Ad.country).distinct()]
    country_opts = sorted(
        [(code, COUNTRIES[code][lang]) for code in used_codes if code in COUNTRIES],
        key=lambda x: x[1],
    )
    years = [r[0] for r in db.session.query(Ad.year).distinct().order_by(Ad.year.desc())]
    categories = Category.query.order_by(
        Category.name_es if lang == "es" else Category.name_en
    ).all()
    return {"country_opts": country_opts, "years": years, "categories": categories}


def _home_feed(lang):
    ads = (
        Ad.query
        .join(Ad.translations).filter(AdTranslation.language == lang)
        .filter(Ad.status == "published")
        .order_by(Ad.created_at.desc(), Ad.year.desc(), Ad.id.desc())
        .all()
    )
    posts = (
        Post.query
        .join(Post.translations).filter(PostTranslation.language == lang)
        .filter(Post.status == "published")
        .filter(Post.published_at != None)
        .filter(Post.published_at <= datetime.utcnow())
        .order_by(Post.published_at.desc(), Post.id.desc())
        .all()
    )
    featured_ads = [ad for ad in ads if ad.is_featured]
    featured_ad = random.choice(featured_ads) if featured_ads else (ads[0] if ads else None)
    latest_ads = [ad for ad in ads if not featured_ad or ad.id != featured_ad.id][:4]
    return {
        "featured_ad": featured_ad,
        "latest_ads": latest_ads,
        "featured_post": posts[0] if posts else None,
        "featured_posts": posts[1:3] if len(posts) > 1 else [],
        "latest_posts": posts[3:7],
    }


def _is_new_ad(ad):
    return bool(ad and ad.created_at and datetime.utcnow() - ad.created_at <= timedelta(days=7))


def _subscribe(lang):
    email = request.form.get("email", "").strip().lower()
    if not email or "@" not in email:
        msg = "Por favor ingresa un email válido." if lang == "es" else "Please enter a valid email."
        flash(msg, "error")
        return False
    if NewsletterSubscriber.query.filter_by(email=email).first():
        flash("Ya estás suscrito." if lang == "es" else "You're already subscribed.", "info")
        return False
    db.session.add(NewsletterSubscriber(email=email, language=lang))
    db.session.commit()
    flash("¡Suscrito! Gracias." if lang == "es" else "Subscribed! Thank you.", "success")
    return True


def _rating_value(name):
    raw = request.form.get(name, "").strip()
    if not raw.isdigit():
        return None
    value = int(raw)
    return value if 1 <= value <= 5 else None


def _comment_is_editable(comment):
    if comment is None or comment.created_at is None:
        return False
    return datetime.utcnow() - comment.created_at <= timedelta(minutes=5)


def _set_comment_translation(comment, body, source_lang):
    target_lang = "en" if source_lang == "es" else "es"
    translated_body, provider = translate_text(body, source_lang, target_lang)
    comment.body_language = source_lang
    comment.translated_body = translated_body
    comment.translated_language = target_lang if translated_body else None
    comment.translation_provider = provider


def _critique_access_for_ad(user, ad, existing_comment=None):
    if not user.is_authenticated:
        return False, False, None
    if user.role in ("admin", "editor", "approver"):
        return True, False, None
    if user.role != "gold":
        return False, False, None
    if existing_comment:
        return True, False, None
    if not user.gold_started_at or not ad.created_at:
        return True, False, None
    if ad.created_at >= user.gold_started_at:
        return True, False, None
    if not user.gold_intro_critique_used:
        return True, True, "intro"
    return False, False, "locked_by_date"


def _handle_ad_detail(lang, slug):
    ui = CATALOG_UI[lang]
    ad = Ad.query.filter_by(slug=slug).first_or_404()
    if ad.status != "published":
        abort(404)
    t = ad.translation(lang)
    if t is None:
        abort(404)

    can_read    = can_read_ad_analysis(ad)
    can_comment = can_comment_on_ad()
    existing_user_comment = None
    user_comment_editable = False
    if current_user.is_authenticated:
        existing_user_comment = AdComment.query.filter_by(
            ad_id=ad.id, user_id=current_user.id
        ).order_by(AdComment.created_at.asc()).first()
        user_comment_editable = _comment_is_editable(existing_user_comment)
    can_submit_critique, uses_intro_critique, critique_block_reason = _critique_access_for_ad(
        current_user, ad, existing_user_comment
    )

    detail_route = f"main.ad_detail_{lang}"
    alt_lang     = "en" if lang == "es" else "es"
    alt_route    = f"main.ad_detail_{alt_lang}"

    if request.method == "POST":
        if "body" in request.form:
            # Comment submission
            if not can_comment or not can_submit_critique:
                abort(403)
            body = request.form.get("body", "").strip()
            if not body:
                flash(ui["comment_err"], "error")
            elif existing_user_comment and not user_comment_editable:
                flash(ui["comment_locked"], "error")
            elif any(_rating_value(field) is None for field in (
                "rating_music", "rating_art_direction",
                "rating_copywriting", "rating_strategy",
            )):
                flash(ui["rating_err"], "error")
            else:
                from app.moderation import comment_status_for_text
                status = comment_status_for_text(body)
                comment = existing_user_comment or AdComment(
                    ad_id=ad.id, user_id=current_user.id
                )
                comment.body = body
                comment.status = status
                comment.rating_music = _rating_value("rating_music")
                comment.rating_art_direction = _rating_value("rating_art_direction")
                comment.rating_copywriting = _rating_value("rating_copywriting")
                comment.rating_strategy = _rating_value("rating_strategy")
                _set_comment_translation(comment, body, lang)
                if existing_user_comment is None:
                    db.session.add(comment)
                    if uses_intro_critique and current_user.role == "gold":
                        current_user.gold_intro_critique_used = True
                db.session.commit()
                if existing_user_comment:
                    flash(ui["comment_updated"], "success")
                else:
                    flash(ui["comment_pending"] if status == "pending" else ui["comment_ok"],
                          "info" if status == "pending" else "success")
            return redirect(url_for(detail_route, slug=slug) + "#comentarios")
        else:
            # Newsletter subscribe
            _subscribe(lang)
            return redirect(url_for(detail_route, slug=slug))

    comments = ad.comments.filter_by(status="approved").all()

    return render_template(
        f"{lang}/ad_detail.html",
        ad=ad, t=t, lang=lang,
        alt_lang_url=url_for(alt_route, slug=slug),
        country_name=country_name,
        is_new_ad=_is_new_ad,
        can_read=can_read,
        can_comment=can_comment,
        ui=ui,
        comments=comments,
        language_name=language_name,
        existing_user_comment=existing_user_comment,
        user_comment_editable=user_comment_editable,
        can_submit_critique=can_submit_critique,
        uses_intro_critique=uses_intro_critique,
        critique_block_reason=critique_block_reason,
    )


# ---------------------------------------------------------------------------
# Root redirect
# ---------------------------------------------------------------------------

@main.route("/")
def root():
    return redirect(url_for("main.gallery_es"))


# ---------------------------------------------------------------------------
# Spanish routes
# ---------------------------------------------------------------------------

@main.route("/es/", methods=["GET", "POST"])
def gallery_es():
    lang = "es"
    if request.method == "POST":
        _subscribe(lang)
        return redirect(url_for("main.gallery_es"))

    home = _home_feed(lang)
    return render_template(
        "es/gallery.html",
        home=home,
        lang=lang,
        alt_lang_url=url_for("main.gallery_en"),
        country_name=country_name,
        is_new_ad=_is_new_ad,
    )


@main.route("/es/criticas/", methods=["GET", "POST"])
def catalog_es():
    lang = "es"
    if request.method == "POST":
        _subscribe(lang)
        return redirect(url_for("main.catalog_es"))

    ads, filters = _filtered_ads(lang)
    options = _filter_options(lang)
    return render_template(
        "es/catalog.html",
        ads=ads, filters=filters, options=options,
        lang=lang,
        alt_lang_url=url_for("main.catalog_en"),
        country_name=country_name,
        is_new_ad=_is_new_ad,
    )


@main.route("/es/anuncio/<slug>", methods=["GET", "POST"])
def ad_detail_es(slug):
    return _handle_ad_detail("es", slug)


# ---------------------------------------------------------------------------
# English routes
# ---------------------------------------------------------------------------

@main.route("/en/", methods=["GET", "POST"])
def gallery_en():
    lang = "en"
    if request.method == "POST":
        _subscribe(lang)
        return redirect(url_for("main.gallery_en"))

    home = _home_feed(lang)
    return render_template(
        "en/gallery.html",
        home=home,
        lang=lang,
        alt_lang_url=url_for("main.gallery_es"),
        country_name=country_name,
        is_new_ad=_is_new_ad,
    )


@main.route("/en/critiques/", methods=["GET", "POST"])
def catalog_en():
    lang = "en"
    if request.method == "POST":
        _subscribe(lang)
        return redirect(url_for("main.catalog_en"))

    ads, filters = _filtered_ads(lang)
    options = _filter_options(lang)
    return render_template(
        "en/catalog.html",
        ads=ads, filters=filters, options=options,
        lang=lang,
        alt_lang_url=url_for("main.catalog_es"),
        country_name=country_name,
        is_new_ad=_is_new_ad,
    )


@main.route("/en/ad/<slug>", methods=["GET", "POST"])
def ad_detail_en(slug):
    return _handle_ad_detail("en", slug)


# ---------------------------------------------------------------------------
# Delete own ad comment (public route)
# ---------------------------------------------------------------------------

@main.route("/ad-comentario/<int:comment_id>/eliminar", methods=["POST"])
def delete_ad_comment(comment_id):
    if not current_user.is_authenticated:
        abort(403)
    comment = AdComment.query.get_or_404(comment_id)
    ad = comment.ad
    is_own          = comment.user_id == current_user.id and _comment_is_editable(comment)
    is_admin        = current_user.role == "admin"
    is_editor_owner = current_user.role == "editor" and ad and ad.created_by_id == current_user.id
    if not (is_own or is_admin or is_editor_owner):
        abort(403)
    lang = request.form.get("lang", "es")
    slug = ad.slug if ad else None
    db.session.delete(comment)
    db.session.commit()
    if slug:
        return redirect(url_for(f"main.ad_detail_{lang}", slug=slug) + "#comentarios")
    return redirect(url_for("main.gallery_es"))

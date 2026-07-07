from datetime import datetime, timedelta
import os
import random

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, jsonify
from flask_login import current_user
from app import db
from app.models import (
    Ad,
    AdComment,
    AdCommentLike,
    AdCommentRating,
    AdDebateComment,
    AdTranslation,
    Category,
    Follow,
    NewsletterSubscriber,
    Post,
    PostTranslation,
    SavedAd,
    SavedCritique,
    User,
)
from app.countries import COUNTRIES, country_name, countries_sorted
from app.utils import (
    can_read_ad_analysis, can_comment_on_ad, can_participate_in_debate,
    ensure_username_slug, ensure_critique_slug, sanitize_critique_html,
    save_upload_file,
)
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
        "comment_locked":        "Tu crítica ya quedó cerrada. Solo se puede editar durante las primeras 24 horas.",
        "comment_edit_title":    "Editar tu crítica",
        "comment_locked_title":  "Crítica cerrada",
        "comment_locked_body":   "Cada miembro Gold puede publicar una sola crítica por anuncio. La edición queda abierta por 24 horas después de publicarla.",
        "comment_update_btn":    "Actualizar crítica",
        "comment_edit_window":   "Puedes editarla durante las 24 horas siguientes a su publicación.",
        "translation_notice":    "Se traducirá automáticamente al inglés una vez que publiques tu crítica.",
        "comment_gold_since_title": "Tu membresía Gold marca el corte",
        "comment_gold_since_body":  "Puedes publicar críticas en anuncios agregados desde que eres Gold.",
        "comment_intro_title":      "Crítica de cortesía disponible",
        "comment_intro_body":       "Este anuncio es anterior a tu membresía. Te quedan {remaining} de {limit} críticas retroactivas.",
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
        # Community Critiques (card list on the ad page)
        "community_critiques_title": "Críticas de la comunidad",
        "no_critiques_yet":      "Todavía no hay críticas de la comunidad para este anuncio.",
        "read_critique":         "Leer crítica",
        "publish_critique_cta":  "Publica tu crítica",
        "edit_critique_cta":     "Editar tu crítica",
        "delete_critique_cta":   "Eliminar crítica",
        "become_gold_cta":       "Hazte Gold para publicar tu crítica",
        "debate_link":           "Debate profesional",
        "min_read":              "min de lectura",
        # Individual critique page
        "critique_label":        "Crítica",
        "published_label":       "Publicado",
        "edited_label":          "Editado",
        "campaign_label":        "Campaña",
        "brand_label":           "Marca",
        "year_label":            "Año",
        "like_btn":              "Me gusta",
        "save_btn":              "Guardar",
        "share_btn":             "Compartir",
        "ad_mention_label":      "Sobre el anuncio",
        "follow_btn":            "Seguir crítico",
        "unfollow_btn":          "Siguiendo",
        "original_analysis_title": "Análisis original de AdCritic",
        "official_analysis_label": "Análisis oficial",
        "view_original_analysis":  "Ver análisis original",
        "critiques_published_label": "Críticas publicadas",
        "readers_label":         "Lectores",
        "likes_received_label":  "Likes recibidos",
        "followers_label":       "Seguidores",
        "about_label":           "Sobre",
        "publish_perspective_title": "¿Cuál es tu perspectiva?",
        "publish_perspective_body":  "Publica tu propia crítica y únete a la conversación profesional.",
        "own_critique_title":    "Ya publicaste tu crítica para este anuncio",
        "own_critique_body":     "Solo puedes publicar una crítica por anuncio, pero puedes editar la tuya cuando quieras.",
        "editorial_team":        "Equipo Editorial AdCritic",
        # Professional Debate
        "debate_title":          "Debate profesional",
        "debate_empty":          "Todavía no hay comentarios en este debate.",
        "debate_placeholder":    "Comparte tu punto de vista con otros críticos Gold...",
        "debate_btn":            "Publicar comentario",
        "debate_gold_only_title": "Espacio exclusivo para críticos Gold",
        "debate_gold_only_body":  "El debate profesional es un espacio de discusión entre miembros Gold sobre esta campaña.",
        # Write/edit critique form
        "write_critique_title":     "Escribe tu crítica",
        "write_critique_edit_title": "Edita tu crítica",
        "title_label":            "Título",
        "title_placeholder":      "Un título para tu crítica...",
        "back_to_ad":             "← Volver al anuncio",
        "rating_panel_title":     "Valoración crítica",
        "critique_body_label":    "Tu crítica",
        "average_label":          "Promedio",
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
        "comment_locked":        "Your critique is locked. It can only be edited during the first 24 hours.",
        "comment_edit_title":    "Edit your critique",
        "comment_locked_title":  "Critique closed",
        "comment_locked_body":   "Each Gold member can publish one critique per ad. Editing stays open for 24 hours after posting.",
        "comment_update_btn":    "Update critique",
        "comment_edit_window":   "You can edit it for the 24 hours after posting.",
        "translation_notice":    "This will be automatically translated to Spanish once you publish your critique.",
        "comment_gold_since_title": "Your Gold membership sets the line",
        "comment_gold_since_body":  "You can publish critiques on ads added since you became Gold.",
        "comment_intro_title":      "Courtesy critique available",
        "comment_intro_body":       "This ad predates your membership. You have {remaining} of {limit} retroactive critiques left.",
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
        # Community Critiques (card list on the ad page)
        "community_critiques_title": "Community Critiques",
        "no_critiques_yet":      "No community critiques yet for this ad.",
        "read_critique":         "Read critique",
        "publish_critique_cta":  "Publish your critique",
        "edit_critique_cta":     "Edit your critique",
        "delete_critique_cta":   "Delete critique",
        "become_gold_cta":       "Become Gold to publish your own critique",
        "debate_link":           "Professional Debate",
        "min_read":              "min read",
        # Individual critique page
        "critique_label":        "Critique",
        "published_label":       "Published",
        "edited_label":          "Edited",
        "campaign_label":        "Campaign",
        "brand_label":           "Brand",
        "year_label":            "Year",
        "like_btn":              "Like",
        "save_btn":              "Save",
        "share_btn":             "Share",
        "ad_mention_label":      "About the ad",
        "follow_btn":            "Follow critic",
        "unfollow_btn":          "Following",
        "original_analysis_title": "Original AdCritic Analysis",
        "official_analysis_label": "Official Analysis",
        "view_original_analysis":  "View original analysis",
        "critiques_published_label": "Critiques published",
        "readers_label":         "Readers",
        "likes_received_label":  "Likes received",
        "followers_label":       "Followers",
        "about_label":           "About",
        "publish_perspective_title": "What's your perspective?",
        "publish_perspective_body":  "Publish your own critique and join the professional conversation.",
        "own_critique_title":    "You already published your critique for this ad",
        "own_critique_body":     "You can only publish one critique per ad, but you can edit yours anytime.",
        "editorial_team":        "AdCritic Editorial Team",
        # Professional Debate
        "debate_title":          "Professional Debate",
        "debate_empty":          "No comments in this debate yet.",
        "debate_placeholder":    "Share your perspective with other Gold critics...",
        "debate_btn":            "Post comment",
        "debate_gold_only_title": "Exclusive space for Gold critics",
        "debate_gold_only_body":  "Professional Debate is a discussion space for Gold members about this campaign.",
        # Write/edit critique form
        "write_critique_title":     "Write your critique",
        "write_critique_edit_title": "Edit your critique",
        "title_label":            "Title",
        "title_placeholder":      "A title for your critique...",
        "back_to_ad":             "← Back to the ad",
        "rating_panel_title":     "Critical rating",
        "critique_body_label":    "Your critique",
        "average_label":          "Average",
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


def _critique_is_editable(critique):
    if critique is None or critique.created_at is None:
        return False
    return datetime.utcnow() - critique.created_at <= timedelta(hours=24)


def _set_comment_translation(comment, body, source_lang):
    target_lang = "en" if source_lang == "es" else "es"
    translated_body, provider = translate_text(body, source_lang, target_lang, fmt="html")
    comment.body_language = source_lang
    comment.translated_body = sanitize_critique_html(translated_body) if translated_body else None
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
    if (user.gold_intro_critiques_used or 0) < User.GOLD_INTRO_CRITIQUE_LIMIT:
        return True, True, "intro"
    return False, False, "locked_by_date"


def _handle_ad_detail(lang, slug):
    """Official analysis page for a campaign. Community critiques are shown
    here only as summary cards linking out to their own page — the full
    text, ratings, likes and the write/edit form all live on the critique's
    own route (see _handle_critique_detail / _handle_write_critique)."""
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
    if current_user.is_authenticated:
        existing_user_comment = AdComment.query.filter_by(
            ad_id=ad.id, user_id=current_user.id
        ).order_by(AdComment.created_at.asc()).first()
    existing_comment_editable = _critique_is_editable(existing_user_comment)
    can_submit_critique, uses_intro_critique, critique_block_reason = _critique_access_for_ad(
        current_user, ad, existing_user_comment
    )

    detail_route = f"main.ad_detail_{lang}"
    alt_lang     = "en" if lang == "es" else "es"
    alt_route    = f"main.ad_detail_{alt_lang}"

    if request.method == "POST":
        action = request.form.get("_action", "")
        if action == "toggle_save_ad":
            if not current_user.is_authenticated:
                abort(403)
            existing_save = SavedAd.query.filter_by(ad_id=ad.id, user_id=current_user.id).first()
            if existing_save:
                db.session.delete(existing_save)
            else:
                db.session.add(SavedAd(ad_id=ad.id, user_id=current_user.id))
            db.session.commit()
            return redirect(url_for(detail_route, slug=slug))
        else:
            # Newsletter subscribe
            _subscribe(lang)
            return redirect(url_for(detail_route, slug=slug))

    critiques = ad.comments.filter_by(status="approved").order_by(AdComment.created_at.desc()).all()
    critique_like_counts = {}
    if critiques:
        critique_ids = [c.id for c in critiques]
        like_rows = (
            db.session.query(AdCommentLike.comment_id, db.func.count(AdCommentLike.id))
            .filter(AdCommentLike.comment_id.in_(critique_ids))
            .group_by(AdCommentLike.comment_id)
            .all()
        )
        critique_like_counts = {comment_id: count for comment_id, count in like_rows}

    saved_analysis = False
    saved_count = SavedAd.query.filter_by(ad_id=ad.id).count()
    if current_user.is_authenticated:
        saved_analysis = SavedAd.query.filter_by(ad_id=ad.id, user_id=current_user.id).first() is not None

    return render_template(
        f"{lang}/ad_detail.html",
        ad=ad, t=t, lang=lang,
        alt_lang_url=url_for(alt_route, slug=slug),
        country_name=country_name,
        is_new_ad=_is_new_ad,
        can_read=can_read,
        can_comment=can_comment,
        ui=ui,
        critiques=critiques,
        critique_like_counts=critique_like_counts,
        existing_user_comment=existing_user_comment,
        existing_comment_editable=existing_comment_editable,
        can_submit_critique=can_submit_critique,
        uses_intro_critique=uses_intro_critique,
        critique_block_reason=critique_block_reason,
        saved_analysis=saved_analysis,
        saved_count=saved_count,
    )


def _author_stats(user):
    """Aggregate stats shown on a critique's author sidebar."""
    critique_ids = [
        row.id for row in AdComment.query.filter_by(user_id=user.id, status="approved").all()
    ]
    likes_received = 0
    readers = 0
    if critique_ids:
        likes_received = (
            AdCommentLike.query.filter(AdCommentLike.comment_id.in_(critique_ids)).count()
        )
        readers = (
            db.session.query(db.func.coalesce(db.func.sum(AdComment.reads_count), 0))
            .filter(AdComment.id.in_(critique_ids))
            .scalar()
        )
    return {
        "critiques_published": len(critique_ids),
        "likes_received": likes_received,
        "readers": readers or 0,
        # People following this critic — not who this critic follows, which
        # isn't a meaningful "reach" stat to show on their public profile.
        "followers": Follow.query.filter_by(followed_id=user.id).count(),
    }


def _handle_critique_detail(lang, username, slug):
    ui = CATALOG_UI[lang]
    critique = AdComment.query.filter_by(slug=slug, status="approved").first_or_404()
    author = critique.user
    ad = critique.ad

    canonical_route = f"main.critique_detail_{lang}"
    if author.username_slug != username:
        return redirect(url_for(canonical_route, username=author.username_slug, slug=slug), code=301)

    alt_lang = "en" if lang == "es" else "es"
    alt_lang_url = url_for(f"main.critique_detail_{alt_lang}", username=author.username_slug, slug=slug)

    if request.method == "POST":
        action = request.form.get("_action", "")
        if not current_user.is_authenticated:
            abort(403)

        if action == "toggle_critique_like":
            existing = AdCommentLike.query.filter_by(
                comment_id=critique.id, user_id=current_user.id
            ).first()
            if existing:
                db.session.delete(existing)
            else:
                db.session.add(AdCommentLike(comment_id=critique.id, user_id=current_user.id))
            db.session.commit()

        elif action == "rate_critique":
            rating = request.form.get("rating", type=int)
            if rating is not None and 1 <= rating <= 5:
                existing_rating = AdCommentRating.query.filter_by(
                    comment_id=critique.id, user_id=current_user.id
                ).first()
                if existing_rating:
                    existing_rating.rating = rating
                else:
                    db.session.add(AdCommentRating(
                        comment_id=critique.id, user_id=current_user.id, rating=rating,
                    ))
                db.session.commit()

        elif action == "toggle_save_critique":
            existing = SavedCritique.query.filter_by(
                critique_id=critique.id, user_id=current_user.id
            ).first()
            if existing:
                db.session.delete(existing)
            else:
                db.session.add(SavedCritique(critique_id=critique.id, user_id=current_user.id))
            db.session.commit()

        elif action == "toggle_follow":
            target_id = request.form.get("user_id", type=int)
            if target_id and target_id != current_user.id:
                existing = Follow.query.filter_by(
                    follower_id=current_user.id, followed_id=target_id
                ).first()
                if existing:
                    db.session.delete(existing)
                else:
                    db.session.add(Follow(follower_id=current_user.id, followed_id=target_id))
                db.session.commit()

        return redirect(url_for(canonical_route, username=username, slug=slug))

    # One increment per view — no de-dup for v1.
    critique.reads_count = (critique.reads_count or 0) + 1
    db.session.commit()

    like_count = AdCommentLike.query.filter_by(comment_id=critique.id).count()
    liked = (
        current_user.is_authenticated
        and AdCommentLike.query.filter_by(comment_id=critique.id, user_id=current_user.id).first() is not None
    )
    saved = (
        current_user.is_authenticated
        and SavedCritique.query.filter_by(critique_id=critique.id, user_id=current_user.id).first() is not None
    )
    following_author = (
        current_user.is_authenticated
        and Follow.query.filter_by(follower_id=current_user.id, followed_id=author.id).first() is not None
    )
    # The viewer's own critique for this same ad, if any — may be this very
    # critique (viewing your own page) or a different one (you critiqued
    # this ad too and are now reading someone else's take on it). Either
    # way, the CTA must offer to edit it, not pretend a new one can be
    # published (only one critique per ad per member).
    viewer_existing_comment = None
    if current_user.is_authenticated:
        viewer_existing_comment = AdComment.query.filter_by(
            ad_id=ad.id, user_id=current_user.id
        ).order_by(AdComment.created_at.asc()).first()
    viewer_comment_editable = _critique_is_editable(viewer_existing_comment)
    can_submit_critique, _, _ = _critique_access_for_ad(current_user, ad, viewer_existing_comment)

    return render_template(
        f"{lang}/critique_detail.html",
        lang=lang, ui=ui, minimal_header=True,
        critique=critique, ad=ad, t=ad.translation(lang),
        country_name=country_name,
        author=author, author_stats=_author_stats(author),
        like_count=like_count, liked=liked, saved=saved,
        following_author=following_author,
        can_submit_critique=can_submit_critique,
        viewer_existing_comment=viewer_existing_comment,
        viewer_comment_editable=viewer_comment_editable,
        google_maps_embed_key=os.environ.get("GOOGLE_MAPS_EMBED_KEY", ""),
        alt_lang_url=alt_lang_url,
    )


def _handle_write_critique(lang, ad_slug):
    ui = CATALOG_UI[lang]
    ad = Ad.query.filter_by(slug=ad_slug).first_or_404()
    if not can_comment_on_ad():
        abort(403)

    existing_user_comment = AdComment.query.filter_by(
        ad_id=ad.id, user_id=current_user.id
    ).order_by(AdComment.created_at.asc()).first()
    critique_editable = _critique_is_editable(existing_user_comment)
    can_submit_critique, uses_intro_critique, critique_block_reason = _critique_access_for_ad(
        current_user, ad, existing_user_comment
    )
    if not can_submit_critique:
        abort(403)
    if existing_user_comment and not critique_editable:
        abort(403)

    if request.method == "POST":
        import re
        title = request.form.get("title", "").strip()
        body = sanitize_critique_html(request.form.get("body", "")).strip()
        body_text = re.sub(r"<[^>]+>", " ", body).strip()
        if not title or not body_text:
            flash(ui["comment_err"], "error")
        elif any(_rating_value(field) is None for field in (
            "rating_music", "rating_art_direction",
            "rating_copywriting", "rating_strategy",
        )):
            flash(ui["rating_err"], "error")
        else:
            from app.moderation import comment_status_for_text
            status = comment_status_for_text(body_text)
            critique = existing_user_comment or AdComment(ad_id=ad.id, user_id=current_user.id)
            critique.title = title
            critique.body = body
            critique.status = status
            critique.rating_music = _rating_value("rating_music")
            critique.rating_art_direction = _rating_value("rating_art_direction")
            critique.rating_copywriting = _rating_value("rating_copywriting")
            critique.rating_strategy = _rating_value("rating_strategy")
            _set_comment_translation(critique, body, lang)
            is_new = existing_user_comment is None
            if is_new:
                db.session.add(critique)
                if uses_intro_critique and current_user.role == "gold":
                    current_user.gold_intro_critiques_used = (current_user.gold_intro_critiques_used or 0) + 1
            else:
                critique.updated_at = datetime.utcnow()
            ensure_username_slug(current_user)
            db.session.flush()
            ensure_critique_slug(critique)
            db.session.commit()
            flash(ui["comment_updated"] if not is_new else
                  (ui["comment_pending"] if status == "pending" else ui["comment_ok"]),
                  "success" if status != "pending" else "info")
            return redirect(url_for(
                f"main.critique_detail_{lang}",
                username=current_user.username_slug, slug=critique.slug,
            ))

    intro_remaining = User.GOLD_INTRO_CRITIQUE_LIMIT - (current_user.gold_intro_critiques_used or 0)
    return render_template(
        f"{lang}/write_critique.html",
        lang=lang, ui=ui, ad=ad, t=ad.translation(lang),
        existing_user_comment=existing_user_comment,
        uses_intro_critique=uses_intro_critique,
        intro_remaining=intro_remaining,
        intro_limit=User.GOLD_INTRO_CRITIQUE_LIMIT,
    )


@main.route("/critica/subir-imagen", methods=["POST"])
def upload_critique_image():
    """Image upload target for the critique rich-text editor. Gold/staff
    only — same gate as writing a critique at all."""
    if not can_comment_on_ad():
        abort(403)
    mf, err = save_upload_file(request.files.get("file"), allowed_types={"image"})
    if err:
        return jsonify({"error": err}), 400
    db.session.commit()
    return jsonify({"location": mf.url})


def _handle_ad_debate(lang, ad_slug):
    ui = CATALOG_UI[lang]
    ad = Ad.query.filter_by(slug=ad_slug).first_or_404()
    allowed = can_participate_in_debate()

    if request.method == "POST":
        if not allowed:
            abort(403)
        body = request.form.get("body", "").strip()
        if body:
            from app.moderation import comment_status_for_text
            db.session.add(AdDebateComment(
                ad_id=ad.id, user_id=current_user.id, body=body,
                status=comment_status_for_text(body),
            ))
            db.session.commit()
        return redirect(url_for(f"main.ad_debate_{lang}", ad_slug=ad_slug))

    debate_comments = []
    if allowed:
        debate_comments = (
            AdDebateComment.query
            .filter_by(ad_id=ad.id, status="approved")
            .order_by(AdDebateComment.created_at.asc())
            .all()
        )

    return render_template(
        f"{lang}/ad_debate.html",
        lang=lang, ui=ui, ad=ad, t=ad.translation(lang),
        allowed=allowed, debate_comments=debate_comments,
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


@main.route("/es/campana/@<username>/<slug>", methods=["GET", "POST"])
def critique_detail_es(username, slug):
    return _handle_critique_detail("es", username, slug)


@main.route("/es/anuncio/<ad_slug>/escribir-critica", methods=["GET", "POST"])
def write_critique_es(ad_slug):
    return _handle_write_critique("es", ad_slug)


@main.route("/es/anuncio/<ad_slug>/debate", methods=["GET", "POST"])
def ad_debate_es(ad_slug):
    return _handle_ad_debate("es", ad_slug)


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


@main.route("/en/ad-campaign/@<username>/<slug>", methods=["GET", "POST"])
def critique_detail_en(username, slug):
    return _handle_critique_detail("en", username, slug)


@main.route("/en/ad/<ad_slug>/write-critique", methods=["GET", "POST"])
def write_critique_en(ad_slug):
    return _handle_write_critique("en", ad_slug)


@main.route("/en/ad/<ad_slug>/debate", methods=["GET", "POST"])
def ad_debate_en(ad_slug):
    return _handle_ad_debate("en", ad_slug)


# ---------------------------------------------------------------------------
# Delete own ad comment (public route)
# ---------------------------------------------------------------------------

@main.route("/ad-comentario/<int:comment_id>/eliminar", methods=["POST"])
def delete_ad_comment(comment_id):
    if not current_user.is_authenticated:
        abort(403)
    comment = AdComment.query.get_or_404(comment_id)
    ad = comment.ad
    author = comment.user
    is_own          = comment.user_id == current_user.id and _critique_is_editable(comment)
    is_admin        = current_user.role == "admin"
    is_editor_owner = current_user.role == "editor" and ad and ad.created_by_id == current_user.id
    if not (is_own or is_admin or is_editor_owner):
        abort(403)
    lang = request.form.get("lang", "es")
    slug = ad.slug if ad else None
    # If this critique had used one of the author's 3 retroactive/intro
    # slots (an ad older than their Gold start date), refund it — deleting
    # within the window should give them a genuine do-over, not a
    # permanently spent slot for a critique that no longer exists.
    if (author and author.role == "gold" and ad and ad.created_at and author.gold_started_at
            and ad.created_at < author.gold_started_at):
        author.gold_intro_critiques_used = max(0, (author.gold_intro_critiques_used or 0) - 1)
    db.session.delete(comment)
    db.session.commit()
    if slug:
        return redirect(url_for(f"main.ad_detail_{lang}", slug=slug) + "#community-critiques")
    return redirect(url_for("main.gallery_es"))

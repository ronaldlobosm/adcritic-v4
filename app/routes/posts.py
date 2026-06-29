from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import current_user
from app import db
from app.models import Post, PostTranslation, PostCategory, PostComment, BannedWord
from app.utils import can_read_post

posts_bp = Blueprint("posts", __name__)

# ---------------------------------------------------------------------------
# UI strings
# ---------------------------------------------------------------------------

UI = {
    "es": {
        "page_title":       "Noticias",
        "subtitle":         "Análisis, tendencias e industria publicitaria.",
        "filter_all":       "Todas las categorías",
        "read_more":        "Leer más →",
        "gold_badge":       "Gold",
        "back_link":        "← Noticias",
        "paywall_title":    "Contenido exclusivo para miembros Gold",
        "paywall_body":     "Este artículo está disponible solo para suscriptores Gold. Apoya el proyecto y accede a todo el contenido.",
        "paywall_cta":      "Ver planes de membresía",
        "paywall_url_es":   "/es/membresia/",
        "comments_title":   "Comentarios",
        "comment_empty":    "Sé el primero en comentar.",
        "comment_placeholder": "Escribe tu comentario...",
        "comment_btn":      "Publicar comentario",
        "comment_login":    "Inicia sesión para dejar un comentario.",
        "comment_login_link": "Iniciar sesión",
        "comment_ok":       "Comentario publicado.",
        "comment_err":      "El comentario no puede estar vacío.",
        "comment_pending":  "Tu comentario está pendiente de revisión.",
        "comment_delete_confirm": "¿Eliminar tu comentario? No se puede deshacer.",
        "comment_delete_ok": "Comentario eliminado.",
        "by":               "Por",
    },
    "en": {
        "page_title":       "News",
        "subtitle":         "Analysis, trends and the advertising industry.",
        "filter_all":       "All categories",
        "read_more":        "Read more →",
        "gold_badge":       "Gold",
        "back_link":        "← News",
        "paywall_title":    "Gold member exclusive content",
        "paywall_body":     "This article is available to Gold subscribers only. Support the project and access all content.",
        "paywall_cta":      "View membership plans",
        "paywall_url_en":   "/en/membership/",
        "comments_title":   "Comments",
        "comment_empty":    "Be the first to comment.",
        "comment_placeholder": "Write your comment...",
        "comment_btn":      "Post comment",
        "comment_login":    "Sign in to leave a comment.",
        "comment_login_link": "Sign in",
        "comment_ok":       "Comment posted.",
        "comment_err":      "Comment cannot be empty.",
        "comment_pending":  "Your comment is pending review.",
        "comment_delete_confirm": "Delete your comment? This cannot be undone.",
        "comment_delete_ok": "Comment deleted.",
        "by":               "By",
    },
}


def _published_posts(lang):
    from app.models import PostTranslation
    return (
        Post.query
        .join(Post.translations).filter(PostTranslation.language == lang)
        .filter(Post.status == "published")
        .filter(Post.published_at != None)
        .filter(Post.published_at <= datetime.utcnow())
        .order_by(Post.published_at.desc())
    )


def _post_categories():
    return PostCategory.query.order_by(PostCategory.name_es).all()


def _handle_list(lang):
    from app.routes.main import _subscribe
    ui = UI[lang]
    alt = url_for("posts.list_en") if lang == "es" else url_for("posts.list_es")

    if request.method == "POST" and request.form.get("newsletter"):
        _subscribe(lang)
        return redirect(request.url)

    cat_id = request.args.get("category_id", "").strip()
    query = _published_posts(lang)
    if cat_id and cat_id.isdigit():
        query = query.filter(Post.categories.any(PostCategory.id == int(cat_id)))

    # "Most read" — currently ordered by views_count desc; falls back gracefully
    # to published_at desc when all views_count are 0 (no real traffic yet).
    # TODO: once views_count accumulates real data, remove the published_at fallback.
    most_read = (
        _published_posts(lang)
        .order_by(Post.views_count.desc(), Post.published_at.desc())
        .limit(5)
        .all()
    )

    return render_template(
        f"{lang}/posts_list.html",
        lang=lang,
        ui=ui,
        alt_lang_url=alt,
        posts=query.all(),
        categories=_post_categories(),
        active_cat_id=cat_id,
        most_read=most_read,
    )


@posts_bp.route("/es/noticias/", methods=["GET", "POST"])
def list_es():
    return _handle_list("es")


@posts_bp.route("/en/news/", methods=["GET", "POST"])
def list_en():
    return _handle_list("en")


def _handle_detail(lang, slug):
    ui = UI[lang]
    post = Post.query.filter_by(slug=slug).first_or_404()

    if not post.is_published:
        abort(404)

    # Increment view counter (only on GET to avoid counting form re-submissions)
    if request.method == "GET":
        post.views_count = (post.views_count or 0) + 1
        db.session.commit()

    t = post.translation(lang)
    if t is None:
        abort(404)

    can_read = can_read_post(post)

    alt_slug = slug
    if lang == "es":
        alt_url = url_for("posts.detail_en", slug=alt_slug)
    else:
        alt_url = url_for("posts.detail_es", slug=alt_slug)

    if request.method == "POST":
        if not current_user.is_authenticated or not can_read:
            abort(403)
        body = request.form.get("body", "").strip()
        if not body:
            flash(ui["comment_err"], "error")
        else:
            from app.moderation import comment_status_for_text
            status = comment_status_for_text(body)
            db.session.add(PostComment(
                post_id=post.id, user_id=current_user.id,
                body=body, status=status,
            ))
            db.session.commit()
            if status == "pending":
                flash(ui["comment_pending"], "info")
            else:
                flash(ui["comment_ok"], "success")
        return redirect(url_for(f"posts.detail_{lang}", slug=slug) + "#comentarios")

    comments = post.comments.filter_by(status="approved").all() if can_read else []

    return render_template(
        f"{lang}/post_detail.html",
        lang=lang,
        ui=ui,
        alt_lang_url=alt_url,
        post=post,
        t=t,
        can_read=can_read,
        comments=comments,
        paywall_url=(ui.get("paywall_url_es") or ui.get("paywall_url_en")),
    )


@posts_bp.route("/es/noticias/<slug>", methods=["GET", "POST"])
def detail_es(slug):
    return _handle_detail("es", slug)


@posts_bp.route("/en/news/<slug>", methods=["GET", "POST"])
def detail_en(slug):
    return _handle_detail("en", slug)


@posts_bp.route("/comentario/<int:comment_id>/eliminar", methods=["POST"])
def delete_comment(comment_id):
    if not current_user.is_authenticated:
        abort(403)
    comment = PostComment.query.get_or_404(comment_id)
    post = comment.post
    is_own       = comment.user_id == current_user.id
    is_admin     = current_user.role == "admin"
    is_editor_owner = current_user.role == "editor" and post and post.author_id == current_user.id
    if not (is_own or is_admin or is_editor_owner):
        abort(403)
    lang = request.form.get("lang", "es")
    slug = comment.post.slug if comment.post else None
    db.session.delete(comment)
    db.session.commit()
    if slug:
        return redirect(url_for(f"posts.detail_{lang}", slug=slug) + "#comentarios")
    return redirect(url_for("posts.list_es"))

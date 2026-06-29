"""Media library — upload, list, delete, picker API, metadata."""
import os
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, jsonify, current_app,
)
from app import db
from app.models import MediaFile
from app.utils import save_upload_file, upload_dir
from app.routes.admin import admin_required, get_admin_lang, ADMIN_UI

media_bp = Blueprint("media", __name__, url_prefix="/admin/media")


# ---------------------------------------------------------------------------
# Media library grid
# ---------------------------------------------------------------------------

@media_bp.route("/")
@admin_required
def index():
    lang = get_admin_lang()
    ui = ADMIN_UI[lang]
    files = MediaFile.query.order_by(MediaFile.uploaded_at.desc()).all()
    return render_template(
        "admin/media.html", lang=lang, ui=ui, active="media", files=files,
    )


# ---------------------------------------------------------------------------
# Upload (JSON response)
# ---------------------------------------------------------------------------

@media_bp.route("/upload", methods=["POST"])
@admin_required
def upload():
    f = request.files.get("file")
    mf, err = save_upload_file(f)
    if err:
        return jsonify({"error": err}), 400
    db.session.commit()
    return jsonify(mf.to_json())


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

@media_bp.route("/<int:file_id>/delete", methods=["POST"])
@admin_required
def delete(file_id):
    mf = MediaFile.query.get_or_404(file_id)
    try:
        save_dir = upload_dir(mf.file_type)
        for fname in (mf.filename, mf.thumbnail):
            if fname:
                path = os.path.join(save_dir, fname)
                if os.path.exists(path):
                    os.remove(path)
    except Exception:
        pass
    db.session.delete(mf)
    db.session.commit()
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"ok": True})
    flash("Archivo eliminado.", "success")
    return redirect(url_for("media.index"))


# ---------------------------------------------------------------------------
# Update metadata
# ---------------------------------------------------------------------------

@media_bp.route("/<int:file_id>/update", methods=["POST"])
@admin_required
def update(file_id):
    mf = MediaFile.query.get_or_404(file_id)
    mf.title_es    = request.form.get("title_es",    "").strip() or None
    mf.title_en    = request.form.get("title_en",    "").strip() or None
    mf.alt_text_es = request.form.get("alt_text_es", "").strip() or None
    mf.alt_text_en = request.form.get("alt_text_en", "").strip() or None
    mf.description = request.form.get("description", "").strip() or None
    db.session.commit()
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"ok": True})
    flash("Metadatos guardados.", "success")
    return redirect(url_for("media.index"))


# ---------------------------------------------------------------------------
# API — single file detail (for metadata edit modal)
# ---------------------------------------------------------------------------

@media_bp.route("/api/file/<int:file_id>")
@admin_required
def api_file(file_id):
    mf = MediaFile.query.get_or_404(file_id)
    return jsonify(mf.to_json())


# ---------------------------------------------------------------------------
# Dedicated video upload endpoint (XHR with progress, async from form)
# ---------------------------------------------------------------------------

@media_bp.route("/upload-video", methods=["POST"])
@admin_required
def upload_video():
    """
    Receives a video file via XHR, transcodes via ffmpeg, returns the final URL.
    The form stores this URL in a hidden field; no re-upload happens on submit.
    """
    f = request.files.get("file")
    mf, err = save_upload_file(f, allowed_types={"video"})
    if err:
        return jsonify({"error": err}), 400
    db.session.commit()
    return jsonify({"url": mf.url, "id": mf.id, "filename": mf.original_filename})


# ---------------------------------------------------------------------------
# API — image list for picker modal
# ---------------------------------------------------------------------------

@media_bp.route("/api/images")
@admin_required
def api_images():
    images = (MediaFile.query
              .filter_by(file_type="image")
              .order_by(MediaFile.uploaded_at.desc())
              .all())
    return jsonify([m.to_json() for m in images])

import os
import uuid
import subprocess
from flask import current_app
from flask_login import current_user
from werkzeug.utils import secure_filename


# ---------------------------------------------------------------------------
# Post access
# ---------------------------------------------------------------------------

def can_read_post(post):
    """Single source of truth for post access."""
    if not post.is_premium:
        return True
    if not current_user.is_authenticated:
        return False
    return current_user.role in ("gold", "admin", "editor")


def can_read_ad_analysis(ad):
    """Returns True if current user can read the full analysis text for a catalog entry."""
    if not ad.is_premium:
        return True
    if not current_user.is_authenticated:
        return False
    return current_user.role in ("gold", "admin", "editor")


def can_comment_on_ad():
    """Returns True if current user may write comments on catalog entries.
    Gold-exclusive: only gold + all staff roles (admin/editor/approver)."""
    if not current_user.is_authenticated:
        return False
    return current_user.role in ("gold", "admin", "editor", "approver")


def can_participate_in_debate():
    """Professional Debate is Gold-only (+staff) to read AND write — unlike
    critiques, Free users have no access at all."""
    if not current_user.is_authenticated:
        return False
    return current_user.role in ("gold", "admin", "editor", "approver")


# ---------------------------------------------------------------------------
# Slugs (critic usernames, critique URLs)
# ---------------------------------------------------------------------------

def slugify(text_value):
    """Lowercase, hyphenated, URL-safe version of a string."""
    import re
    value = (text_value or "").strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "item"


def ensure_username_slug(user):
    """Generate and assign user.username_slug if it doesn't have one yet.
    Does not commit — caller is responsible for committing the session."""
    from app.models import User

    if user.username_slug:
        return user.username_slug

    base = slugify(user.display_name or user.email.split("@")[0])
    candidate = base
    i = 2
    while User.query.filter(User.username_slug == candidate, User.id != user.id).first():
        candidate = f"{base}-{i}"
        i += 1
    user.username_slug = candidate
    return candidate


def ensure_critique_slug(critique):
    """Generate and assign critique.slug (and a fallback title) if missing.
    Does not commit — caller is responsible for committing the session."""
    from app.models import AdComment

    if critique.slug:
        return critique.slug

    if not critique.title:
        import re
        plain = re.sub(r"<[^>]+>", " ", critique.body or "")
        words = plain.split()
        critique.title = " ".join(words[:8]) or f"Critique #{critique.id or ''}"

    base = slugify(critique.title)
    candidate = base
    i = 2
    while AdComment.query.filter(AdComment.slug == candidate, AdComment.id != critique.id).first():
        candidate = f"{base}-{i}"
        i += 1
    critique.slug = candidate
    return candidate


# ---------------------------------------------------------------------------
# Content safety — critique body (rich text from TinyMCE)
# ---------------------------------------------------------------------------

CRITIQUE_HTML_TAGS = [
    "p", "br", "strong", "b", "em", "i", "u", "s", "blockquote",
    "ul", "ol", "li", "a", "img", "h2", "h3", "h4", "figure", "figcaption",
]
CRITIQUE_HTML_ATTRS = {
    "a": ["href", "target", "rel"],
    "img": ["src", "alt", "title", "width", "height"],
    # TinyMCE's alignment buttons apply `style="text-align: ..."` — allowing
    # the bare attribute isn't enough with bleach 6+, it also strips style
    # *values* unless a CSSSanitizer is given (below), which is what
    # actually restricts this to the text-align property.
    "*": ["style"],
}


def sanitize_critique_html(html):
    """Whitelist-clean HTML coming from the critique rich-text editor before
    it's stored. The body is later rendered with |safe, so an unsanitized
    editor payload would be stored XSS — this is the only thing standing
    between a raw POST body and every reader's browser."""
    import bleach
    from bleach.css_sanitizer import CSSSanitizer

    css_sanitizer = CSSSanitizer(allowed_css_properties=["text-align"])
    return bleach.clean(
        html or "",
        css_sanitizer=css_sanitizer,
        tags=CRITIQUE_HTML_TAGS,
        attributes=CRITIQUE_HTML_ATTRS,
        protocols=["http", "https", "mailto"],
        strip=True,
    )


# ---------------------------------------------------------------------------
# File type validation
# ---------------------------------------------------------------------------

ALLOWED_EXTENSIONS = {
    "image":    {".jpg", ".jpeg", ".png", ".gif"},
    "video":    {".mp4", ".webm", ".mov", ".avi", ".mkv"},
    "subtitle": {".vtt", ".srt"},
}


def classify_file(filename):
    """Return (file_type, ext) or (None, ext) if not allowed."""
    ext = os.path.splitext(filename)[1].lower()
    for ftype, exts in ALLOWED_EXTENSIONS.items():
        if ext in exts:
            return ftype, ext
    return None, ext


def upload_dir(file_type):
    subs = {"image": "images", "video": "videos", "subtitle": "subtitles"}
    base = current_app.config.get(
        "UPLOAD_FOLDER",
        os.path.join(current_app.root_path, "static", "uploads"),
    )
    return os.path.join(base, subs.get(file_type, "images"))


def _cloudinary_enabled():
    return bool(os.environ.get("CLOUDINARY_URL"))


def _cloudinary_resource_type(file_type):
    return {
        "image": "image",
        "video": "video",
        "subtitle": "raw",
    }.get(file_type, "auto")


def _cloudinary_folder(file_type):
    base = current_app.config.get("CLOUDINARY_FOLDER", "adcritic").strip("/")
    subs = {"image": "images", "video": "videos", "subtitle": "subtitles"}
    return f"{base}/{subs.get(file_type, 'files')}"


def _cloudinary_upload(path, file_type, *, public_id=None):
    import cloudinary
    import cloudinary.uploader

    cloudinary.config(secure=True)
    result = cloudinary.uploader.upload(
        path,
        folder=_cloudinary_folder(file_type),
        public_id=public_id,
        resource_type=_cloudinary_resource_type(file_type),
        overwrite=False,
        unique_filename=True,
    )
    return {
        "url": result.get("secure_url") or result.get("url"),
        "public_id": result.get("public_id"),
    }


def _remove_local_file(path):
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except OSError:
        pass


def delete_remote_media_file(media_file):
    if not _cloudinary_enabled():
        return

    import cloudinary
    import cloudinary.uploader

    cloudinary.config(secure=True)
    resource_type = _cloudinary_resource_type(media_file.file_type)
    for public_id, rtype in (
        (media_file.cloudinary_public_id, resource_type),
        (media_file.thumbnail_cloudinary_public_id, "image"),
    ):
        if public_id:
            try:
                cloudinary.uploader.destroy(public_id, resource_type=rtype)
            except Exception as exc:
                current_app.logger.warning("Cloudinary delete failed: %s", exc)


# ---------------------------------------------------------------------------
# Image optimization (Pillow)
# ---------------------------------------------------------------------------

def _optimize_image(save_path):
    """
    - Resize to max 1920px wide (keep aspect ratio)
    - Keep transparent PNGs as PNG
    - Convert other images to JPEG
    - Save at quality 82 (in-place, may change extension to .jpg)
    - Generate 400px-wide thumbnail
    Returns (new_filename, thumb_filename) — new_filename may differ if ext changed.
    """
    from PIL import Image

    with Image.open(save_path) as img:
        has_alpha = (
            img.mode in ("RGBA", "LA")
            or (img.mode == "P" and "transparency" in img.info)
        )
        if has_alpha:
            img = img.convert("RGBA")
        elif img.mode != "RGB":
            img = img.convert("RGB")

        w, h = img.size
        if w > 1920:
            new_h = int(h * 1920 / w)
            img = img.resize((1920, new_h), Image.LANCZOS)
            w, h = img.size

        if has_alpha:
            optimized_path = os.path.splitext(save_path)[0] + ".png"
            img.save(optimized_path, format="PNG", optimize=True)
        else:
            optimized_path = os.path.splitext(save_path)[0] + ".jpg"
            img.save(optimized_path, format="JPEG", quality=82, optimize=True)

        if save_path != optimized_path:
            try:
                os.remove(save_path)
            except OSError:
                pass

        # Thumbnail — 400px wide
        thumb_w = min(w, 400)
        thumb_h = int(h * thumb_w / w)
        img_thumb = img.resize((thumb_w, thumb_h), Image.LANCZOS)

        base = os.path.splitext(os.path.basename(optimized_path))[0]
        if has_alpha:
            thumb_name = base + "_thumb.png"
            thumb_path = os.path.join(os.path.dirname(optimized_path), thumb_name)
            img_thumb.save(thumb_path, format="PNG", optimize=True)
        else:
            thumb_name = base + "_thumb.jpg"
            thumb_path = os.path.join(os.path.dirname(optimized_path), thumb_name)
            img_thumb.save(thumb_path, format="JPEG", quality=78, optimize=True)

    return os.path.basename(optimized_path), thumb_name


# ---------------------------------------------------------------------------
# Video transcoding (ffmpeg → H.264 MP4, max 1920px wide)
# ---------------------------------------------------------------------------

def _get_ffmpeg():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        import shutil
        binary = shutil.which("ffmpeg")
        if binary:
            return binary
        raise RuntimeError(
            "ffmpeg not found. Install imageio-ffmpeg or system ffmpeg."
        )


def _transcode_video(input_path, save_dir):
    """
    Convert to a browser-ready MP4:
    - .mp4   → remux only (copy streams, add faststart). No re-encode — instant.
    - .webm  → already web-compatible, skip entirely.
    - others → re-encode to H.264 with ultrafast preset (fast but larger file).
    Returns (output_filename, success_bool).
    """
    ext = os.path.splitext(input_path)[1].lower()

    # .webm is already browser-native — keep original, no processing needed
    if ext == ".webm":
        return os.path.basename(input_path), True

    ffmpeg = _get_ffmpeg()
    out_name = uuid.uuid4().hex + ".mp4"
    out_path = os.path.join(save_dir, out_name)

    if ext == ".mp4":
        # Remux only: copy video+audio streams, add faststart index — very fast
        cmd = [
            ffmpeg,
            "-i", input_path,
            "-c", "copy",
            "-movflags", "+faststart",
            "-y",
            out_path,
        ]
    else:
        # .mov / .avi / .mkv → re-encode with ultrafast preset
        cmd = [
            ffmpeg,
            "-i", input_path,
            "-vf", "scale='min(iw,1920)':-2",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart",
            "-y",
            out_path,
        ]

    try:
        result = subprocess.run(cmd, capture_output=True, timeout=600)
        ok = result.returncode == 0 and os.path.exists(out_path)
    except subprocess.TimeoutExpired:
        ok = False
    except Exception:
        ok = False

    return out_name, ok


# ---------------------------------------------------------------------------
# Main upload entry point
# ---------------------------------------------------------------------------

def save_upload_file(file_storage, allowed_types=None, uploader_id=None):
    """
    Validate, save, and optimize an uploaded file.
    Returns (MediaFile, error_str). Calls db.session.flush() — caller must commit.
    """
    from app import db
    from app.models import MediaFile

    if not file_storage or not file_storage.filename:
        return None, "No file"

    original = secure_filename(file_storage.filename)
    file_type, ext = classify_file(original)

    if file_type is None:
        allowed = ", ".join(
            e for exts in ALLOWED_EXTENSIONS.values() for e in sorted(exts)
        )
        return None, f"Tipo no permitido: {ext}. Permitidos: {allowed}"

    if allowed_types and file_type not in allowed_types:
        return None, f"Tipo de archivo no permitido aquí: {file_type}"

    unique_name = uuid.uuid4().hex + ext
    save_dir = upload_dir(file_type)
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, unique_name)
    file_storage.save(save_path)

    thumbnail = None

    if file_type == "image" and ext != ".gif":
        try:
            unique_name, thumbnail = _optimize_image(save_path)
            save_path = os.path.join(save_dir, unique_name)
        except Exception as exc:
            current_app.logger.warning("Image optimization failed: %s", exc)

    elif file_type == "video":
        try:
            mp4_name, ok = _transcode_video(save_path, save_dir)
            if ok:
                try:
                    os.remove(save_path)
                except OSError:
                    pass
                unique_name = mp4_name
                save_path = os.path.join(save_dir, mp4_name)
            else:
                current_app.logger.warning("Video transcoding failed; keeping original.")
        except Exception as exc:
            current_app.logger.warning("Video transcoding error: %s", exc)

    file_size = os.path.getsize(save_path)
    remote_url = None
    thumbnail_remote_url = None
    cloudinary_public_id = None
    thumbnail_cloudinary_public_id = None

    if _cloudinary_enabled():
        try:
            uploaded = _cloudinary_upload(save_path, file_type)
            remote_url = uploaded["url"]
            cloudinary_public_id = uploaded["public_id"]

            if thumbnail:
                thumb_path = os.path.join(save_dir, thumbnail)
                uploaded_thumb = _cloudinary_upload(
                    thumb_path,
                    "image",
                    public_id=os.path.splitext(thumbnail)[0],
                )
                thumbnail_remote_url = uploaded_thumb["url"]
                thumbnail_cloudinary_public_id = uploaded_thumb["public_id"]

            _remove_local_file(save_path)
            if thumbnail:
                _remove_local_file(os.path.join(save_dir, thumbnail))
        except Exception as exc:
            current_app.logger.error("Cloudinary upload failed: %s", exc)
            return None, "No se pudo subir el archivo a Cloudinary."

    mf = MediaFile(
        filename=unique_name,
        original_filename=original,
        file_type=file_type,
        uploaded_by=uploader_id if uploader_id is not None else current_user.id,
        file_size=file_size,
        thumbnail=thumbnail,
        remote_url=remote_url,
        thumbnail_remote_url=thumbnail_remote_url,
        cloudinary_public_id=cloudinary_public_id,
        thumbnail_cloudinary_public_id=thumbnail_cloudinary_public_id,
    )
    db.session.add(mf)
    db.session.flush()
    return mf, None

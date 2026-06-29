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


# ---------------------------------------------------------------------------
# File type validation
# ---------------------------------------------------------------------------

ALLOWED_EXTENSIONS = {
    "image":    {".jpg", ".jpeg", ".png"},
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


# ---------------------------------------------------------------------------
# Image optimization (Pillow)
# ---------------------------------------------------------------------------

def _optimize_image(save_path):
    """
    - Resize to max 1920px wide (keep aspect ratio)
    - Convert to JPEG (composite alpha on white if needed)
    - Save at quality 82 (in-place, may change extension to .jpg)
    - Generate 400px-wide thumbnail (_thumb.jpg)
    Returns (new_filename, thumb_filename) — new_filename may differ if ext changed.
    """
    from PIL import Image

    with Image.open(save_path) as img:
        # Flatten transparency onto white
        if img.mode in ("RGBA", "LA", "P"):
            bg = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            mask = img.split()[-1] if img.mode in ("RGBA", "LA") else None
            bg.paste(img, mask=mask)
            img = bg
        elif img.mode != "RGB":
            img = img.convert("RGB")

        w, h = img.size
        if w > 1920:
            new_h = int(h * 1920 / w)
            img = img.resize((1920, new_h), Image.LANCZOS)
            w, h = img.size

        # Always save as JPEG; rename if original ext was .png
        jpg_path = os.path.splitext(save_path)[0] + ".jpg"
        img.save(jpg_path, format="JPEG", quality=82, optimize=True)
        if save_path != jpg_path:
            try:
                os.remove(save_path)
            except OSError:
                pass

        # Thumbnail — 400px wide
        thumb_w = min(w, 400)
        thumb_h = int(h * thumb_w / w)
        img_thumb = img.resize((thumb_w, thumb_h), Image.LANCZOS)

        base = os.path.splitext(os.path.basename(jpg_path))[0]
        thumb_name = base + "_thumb.jpg"
        thumb_path = os.path.join(os.path.dirname(jpg_path), thumb_name)
        img_thumb.save(thumb_path, format="JPEG", quality=78, optimize=True)

    return os.path.basename(jpg_path), thumb_name


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

    if file_type == "image":
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

    mf = MediaFile(
        filename=unique_name,
        original_filename=original,
        file_type=file_type,
        uploaded_by=uploader_id if uploader_id is not None else current_user.id,
        file_size=file_size,
        thumbnail=thumbnail,
    )
    db.session.add(mf)
    db.session.flush()
    return mf, None

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.utils import save_upload_file
from app.models import AdComment, AdCommentLike, AdCommentRating, SavedAd
from app.routes.membership import _get_subscription_info, _plan_label, UI as MEMBERSHIP_UI

account = Blueprint("account", __name__)

UI = {
    "es": {
        "page_title":        "Mi cuenta",
        "gold_page_title":   "Mi cuenta Gold",
        "my_critiques_title": "Mis críticas",
        "my_critiques_empty": "Todavía no has publicado críticas.",
        "my_critiques_intro_available": "Aún tienes disponible tu primera crítica retroactiva.",
        "my_critiques_intro_used": "Ya usaste tu crítica retroactiva o tienes historial previo.",
        "view_critique":     "Ver crítica",
        "label_email":       "Correo electrónico",
        "label_role":        "Plan",
        "role_free":         "Gratuito",
        "role_gold":         "Gold",
        "role_admin":        "Admin",
        "role_editor":       "Editor",
        "role_approver":     "Aprobador",
        "role_advertiser":   "Anunciante",
        # Profile section
        "section_profile":   "Perfil público",
        "label_display_name":"Nombre público",
        "hint_display_name": "Visible en comentarios y publicaciones",
        "label_professional_title": "Cargo o profesión",
        "hint_professional_title": "Visible en tus críticas Gold",
        "label_avatar":      "Foto de perfil",
        "label_bio_es":      "Biografía (ES)",
        "label_bio_en":      "Biografía (EN)",
        "hint_bio":          "Breve descripción pública (opcional)",
        "btn_save_profile":  "Guardar perfil",
        "ok_profile_saved":  "Perfil actualizado.",
        "err_avatar":        "No se pudo subir la imagen.",
        # Password section
        "section_password":  "Cambiar contraseña",
        "label_current_pw":  "Contraseña actual",
        "label_new_pw":      "Nueva contraseña",
        "label_confirm_pw":  "Confirmar nueva contraseña",
        "btn_change_pw":     "Cambiar contraseña",
        "err_wrong_pw":      "La contraseña actual es incorrecta.",
        "err_pw_mismatch":   "Las contraseñas nuevas no coinciden.",
        "err_pw_short":      "La nueva contraseña debe tener al menos 8 caracteres.",
        "err_fields":        "Completa todos los campos.",
        "ok_pw_changed":     "Contraseña actualizada correctamente.",
        # Security section
        "section_security":  "Seguridad",
        "security_soon":     "Próximamente: autenticación biométrica",
        # Membership section (merged from MEMBERSHIP_UI)
        "section_membership": "Tu membresía",
        "label_plan":         "Plan",
        "label_renews":       "Próxima renovación",
        "label_cancels":      "Cancela el",
        "btn_portal":         "Gestionar mi suscripción",
        "portal_note":        "Cambia de plan, cancela o actualiza tu método de pago.",
        "no_subscription":    "No tienes una suscripción activa.",
        "upgrade_link":       "Ver planes",
    },
    "en": {
        "page_title":        "My account",
        "gold_page_title":   "My Gold account",
        "my_critiques_title": "My critiques",
        "my_critiques_empty": "You haven't published critiques yet.",
        "my_critiques_intro_available": "Your first retroactive critique is still available.",
        "my_critiques_intro_used": "Your retroactive critique is already used or you had prior critique history.",
        "view_critique":     "View critique",
        "label_email":       "Email address",
        "label_role":        "Plan",
        "role_free":         "Free",
        "role_gold":         "Gold",
        "role_admin":        "Admin",
        "role_editor":       "Editor",
        "role_approver":     "Approver",
        "role_advertiser":   "Advertiser",
        # Profile section
        "section_profile":   "Public profile",
        "label_display_name":"Display name",
        "hint_display_name": "Shown on comments and posts",
        "label_professional_title": "Title or profession",
        "hint_professional_title": "Shown on your Gold critiques",
        "label_avatar":      "Profile picture",
        "label_bio_es":      "Bio (ES)",
        "label_bio_en":      "Bio (EN)",
        "hint_bio":          "Short public description (optional)",
        "btn_save_profile":  "Save profile",
        "ok_profile_saved":  "Profile updated.",
        "err_avatar":        "Could not upload image.",
        # Password section
        "section_password":  "Change password",
        "label_current_pw":  "Current password",
        "label_new_pw":      "New password",
        "label_confirm_pw":  "Confirm new password",
        "btn_change_pw":     "Change password",
        "err_wrong_pw":      "Current password is incorrect.",
        "err_pw_mismatch":   "New passwords do not match.",
        "err_pw_short":      "New password must be at least 8 characters.",
        "err_fields":        "Please fill in all fields.",
        "ok_pw_changed":     "Password updated successfully.",
        # Security section
        "section_security":  "Security",
        "security_soon":     "Coming soon: biometric authentication",
        # Membership section
        "section_membership": "Your membership",
        "label_plan":         "Plan",
        "label_renews":       "Next renewal",
        "label_cancels":      "Cancels on",
        "btn_portal":         "Manage my subscription",
        "portal_note":        "Change plan, cancel, or update your payment method.",
        "no_subscription":    "You don't have an active subscription.",
        "upgrade_link":       "View plans",
    },
}


def _handle_account(lang):
    ui = UI[lang]
    alt_lang_url = (
        url_for("account.my_account_en") if lang == "es"
        else url_for("account.my_account_es")
    )

    if request.method == "POST":
        action = request.form.get("_action", "")

        # ── Profile update ───────────────────────────────────────────────
        if action == "profile":
            display_name = request.form.get("display_name", "").strip() or None
            professional_title = request.form.get("professional_title", "").strip() or None
            bio_es       = request.form.get("bio_es", "").strip() or None
            bio_en       = request.form.get("bio_en", "").strip() or None

            current_user.display_name       = display_name
            current_user.professional_title = professional_title
            current_user.bio_es             = bio_es
            current_user.bio_en             = bio_en

            avatar_file = request.files.get("avatar_file")
            if avatar_file and avatar_file.filename:
                mf, err = save_upload_file(avatar_file, allowed_types={"image"})
                if mf:
                    current_user.avatar_media_id = mf.id
                else:
                    flash(f"{ui['err_avatar']} {err or ''}", "error")

            db.session.commit()
            flash(ui["ok_profile_saved"], "success")
            return redirect(url_for(f"account.my_account_{lang}"))

        # ── Password change ──────────────────────────────────────────────
        elif action == "password":
            current_pw = request.form.get("current_password", "")
            new_pw     = request.form.get("new_password", "")
            confirm_pw = request.form.get("confirm_password", "")

            if not current_pw or not new_pw or not confirm_pw:
                flash(ui["err_fields"], "error")
            elif not current_user.check_password(current_pw):
                flash(ui["err_wrong_pw"], "error")
            elif new_pw != confirm_pw:
                flash(ui["err_pw_mismatch"], "error")
            elif len(new_pw) < 8:
                flash(ui["err_pw_short"], "error")
            else:
                current_user.set_password(new_pw)
                db.session.commit()
                flash(ui["ok_pw_changed"], "success")
                return redirect(url_for(f"account.my_account_{lang}"))

    role_label = ui.get(f"role_{current_user.role}", current_user.role)

    # Fetch Stripe subscription info for Gold users
    sub_info   = None
    plan_label = None
    if current_user.role == "gold" and current_user.stripe_subscription_id:
        sub_info = _get_subscription_info(current_user)
        if sub_info:
            plan_label = _plan_label(sub_info["price_id"], lang)
    comments = []
    if current_user.role == "gold":
        comments = (
            AdComment.query
            .filter_by(user_id=current_user.id)
            .order_by(AdComment.created_at.desc())
            .all()
        )
    comment_like_counts = {}
    comment_rating_stats = {}
    saved_ads_count = SavedAd.query.filter_by(user_id=current_user.id).count()
    if comments:
        comment_ids = [comment.id for comment in comments]
        like_rows = (
            db.session.query(AdCommentLike.comment_id, db.func.count(AdCommentLike.id))
            .filter(AdCommentLike.comment_id.in_(comment_ids))
            .group_by(AdCommentLike.comment_id)
            .all()
        )
        rating_rows = (
            db.session.query(
                AdCommentRating.comment_id,
                db.func.avg(AdCommentRating.rating),
                db.func.count(AdCommentRating.id),
            )
            .filter(AdCommentRating.comment_id.in_(comment_ids))
            .group_by(AdCommentRating.comment_id)
            .all()
        )
        comment_like_counts = {comment_id: count for comment_id, count in like_rows}
        comment_rating_stats = {
            comment_id: {"avg": round(float(avg or 0), 1), "count": count}
            for comment_id, avg, count in rating_rows
        }

    features = MEMBERSHIP_UI[lang]["features"]

    return render_template(
        f"{lang}/my_account.html",
        lang=lang,
        ui=ui,
        alt_lang_url=alt_lang_url,
        role_label=role_label,
        sub_info=sub_info,
        plan_label=plan_label,
        comments=comments,
        features=features,
        comment_like_counts=comment_like_counts,
        comment_rating_stats=comment_rating_stats,
        saved_ads_count=saved_ads_count,
    )


@account.route("/es/mi-cuenta/", methods=["GET", "POST"])
@login_required
def my_account_es():
    return _handle_account("es")


@account.route("/en/my-account/", methods=["GET", "POST"])
@login_required
def my_account_en():
    return _handle_account("en")


def _handle_my_critiques(lang):
    return redirect(url_for(f"account.my_account_{lang}") + "#mis-criticas")


@account.route("/es/mis-criticas/")
@login_required
def my_critiques_es():
    return _handle_my_critiques("es")


@account.route("/en/my-critiques/")
@login_required
def my_critiques_en():
    return _handle_my_critiques("en")

from datetime import datetime, timedelta

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User
from app.utils import save_upload_file
from app.email import (
    send_internal_signup_notification,
    send_password_reset_email,
    send_verification_email,
)
from app.routes.membership import FOUNDER_CUTOFF_COUNT, _founder_active, _gold_count

auth = Blueprint("auth", __name__)

UI = {
    "es": {
        # Login
        "login_title":       "Iniciar sesión",
        "email_label":       "Correo electrónico",
        "password_label":    "Contraseña",
        "login_btn":         "Entrar",
        "no_account":        "¿No tienes cuenta?",
        "have_account":      "¿Ya tienes cuenta?",
        "register_link":     "Regístrate",
        "login_link":        "Inicia sesión",
        "err_credentials":   "Email o contraseña incorrectos.",
        "err_inactive":      "Esta cuenta ha sido desactivada.",
        "err_fields":        "Completa todos los campos.",
        "ok_login":          "Sesión iniciada.",
        "ok_logout":         "Sesión cerrada.",
        "forgot_link":       "¿Olvidaste tu contraseña?",
        "forgot_title":      "Recuperar contraseña",
        "forgot_body":       "Ingresa tu correo y te enviaremos un enlace para crear una nueva contraseña.",
        "forgot_btn":        "Enviar enlace",
        "forgot_sent":       "Si existe una cuenta con ese correo, te enviaremos un enlace de recuperación.",
        "reset_title":       "Nueva contraseña",
        "reset_btn":         "Guardar contraseña",
        "reset_invalid":     "El enlace no es válido o ya expiró.",
        "reset_ok":          "Tu contraseña fue actualizada. Ya puedes iniciar sesión.",
        # Step 1 — elegir plan
        "step1_title":       "Crea tu cuenta",
        "step1_subtitle":    "Elige cómo quieres empezar",
        "free_name":         "Free",
        "free_desc":         "Acceso a críticas de anuncios, newsletter y comunidad.",
        "free_features":     ["Críticas de anuncios", "Newsletter semanal", "Acceso a la comunidad"],
        "free_cta":          "Registrarme gratis",
        "gold_name":         "Gold",
        "gold_desc":         "Todo lo de Free, más análisis completos y acceso a críticas.",
        "gold_features":     ["Análisis completo de cada anuncio", "Publica críticas", "Artículos exclusivos Gold", "Apoya la crítica publicitaria independiente"],
        "gold_cta":          "Quiero ser Gold",
        "gold_price_hint":   "Desde $6.99 / mes · Precio fundador",
        "founder_counter":   "Quedan {left} de {total} perfiles Founder Gold.",
        "step1_login_prompt": "¿Ya tienes cuenta?",
        # Step 2 — datos de cuenta
        "step2_title":       "Crea tu cuenta",
        "step2_subtitle_free": "Cuenta Free",
        "step2_subtitle_gold": "Cuenta Gold",
        "label_display_name": "Nombre público",
        "hint_display_name":  "Cómo te verán otros usuarios (puedes cambiarlo después)",
        "label_email":       "Correo electrónico",
        "label_password":    "Contraseña",
        "hint_password":     "Mínimo 8 caracteres",
        "label_avatar":      "Foto de perfil",
        "label_bio":         "Sobre ti",
        "hint_optional":     "Opcional — puedes completarlo después desde tu perfil",
        "skip_optional":     "Omitir por ahora",
        "register_btn":      "Crear cuenta",
        "err_email":         "Ese email ya está registrado.",
        "err_fields":        "Completa los campos obligatorios.",
        "err_pw_short":      "La contraseña debe tener al menos 8 caracteres.",
        "err_avatar":        "No se pudo subir la imagen.",
        "ok_registered_free": "¡Cuenta creada! Bienvenido a AdCritic.",
        "ok_registered_gold": "¡Cuenta creada! Ahora elige tu plan Gold.",
        "err_verify_email_send": "La cuenta se creó, pero no pudimos enviar el correo de confirmación. Usa Reenviar correo o avísanos si vuelve a fallar.",
        # Email verification
        "verify_title":       "Verifica tu correo",
        "verify_instruction": "Ingresa el código de 6 dígitos que enviamos a tu correo electrónico.",
        "verify_code_label":  "Código de verificación",
        "verify_btn":         "Verificar mi correo",
        "resend_hint":        "¿No recibiste el correo?",
        "resend_btn":         "Reenviar correo de verificación",
        "days_left_note":     "Tu cuenta será eliminada si no verificas en {n} día(s).",
        "err_invalid_code":   "Código incorrecto. Comprueba el correo o solicita uno nuevo.",
        "err_no_code":        "Ingresa el código de verificación.",
        "err_token_invalid":  "El enlace no es válido o ya fue usado.",
        "ok_verified":        "¡Correo verificado! Tu cuenta está activa.",
        "ok_resent":          "Te enviamos un nuevo correo de verificación.",
        "err_resend":         "No se pudo enviar el correo. Intenta de nuevo más tarde.",
        "already_verified":   "Tu correo ya está verificado.",
        # Banner (in base.html)
        "banner_verify":      "Confirma tu correo para activar tu cuenta.",
        "banner_verify_link": "Verificar ahora",
        "banner_resend":      "Reenviar correo",
    },
    "en": {
        # Login
        "login_title":       "Sign in",
        "email_label":       "Email address",
        "password_label":    "Password",
        "login_btn":         "Sign in",
        "no_account":        "Don't have an account?",
        "have_account":      "Already have an account?",
        "register_link":     "Sign up",
        "login_link":        "Sign in",
        "err_credentials":   "Incorrect email or password.",
        "err_inactive":      "This account has been deactivated.",
        "err_fields":        "Please fill in all fields.",
        "ok_login":          "You're signed in.",
        "ok_logout":         "You've been signed out.",
        "forgot_link":       "Forgot your password?",
        "forgot_title":      "Reset password",
        "forgot_body":       "Enter your email and we'll send you a link to create a new password.",
        "forgot_btn":        "Send link",
        "forgot_sent":       "If an account exists for that email, we'll send a reset link.",
        "reset_title":       "New password",
        "reset_btn":         "Save password",
        "reset_invalid":     "This link is invalid or has expired.",
        "reset_ok":          "Your password was updated. You can sign in now.",
        # Step 1 — choose plan
        "step1_title":       "Create your account",
        "step1_subtitle":    "Choose how you want to get started",
        "free_name":         "Free",
        "free_desc":         "Access ad critiques, the newsletter, and the community.",
        "free_features":     ["Ad critiques", "Weekly newsletter", "Community access"],
        "free_cta":          "Sign up for free",
        "gold_name":         "Gold",
        "gold_desc":         "Everything in Free, plus full analysis and critiques.",
        "gold_features":     ["Full analysis of every ad", "Post critiques", "Gold-exclusive articles", "Support independent ad criticism"],
        "gold_cta":          "I want Gold",
        "gold_price_hint":   "From $6.99 / month · Founder price",
        "founder_counter":   "{left} of {total} Founder Gold profiles left.",
        "step1_login_prompt": "Already have an account?",
        # Step 2 — account data
        "step2_title":       "Create your account",
        "step2_subtitle_free": "Free account",
        "step2_subtitle_gold": "Gold account",
        "label_display_name": "Display name",
        "hint_display_name":  "How other users will see you (you can change this later)",
        "label_email":       "Email address",
        "label_password":    "Password",
        "hint_password":     "At least 8 characters",
        "label_avatar":      "Profile picture",
        "label_bio":         "About you",
        "hint_optional":     "Optional — you can complete this later from your profile",
        "skip_optional":     "Skip for now",
        "register_btn":      "Create account",
        "err_email":         "That email is already registered.",
        "err_fields":        "Please fill in the required fields.",
        "err_pw_short":      "Password must be at least 8 characters.",
        "err_avatar":        "Could not upload the image.",
        "ok_registered_free": "Account created! Welcome to AdCritic.",
        "ok_registered_gold": "Account created! Now choose your Gold plan.",
        "err_verify_email_send": "The account was created, but we could not send the confirmation email. Use Resend email or contact us if it keeps failing.",
        # Email verification
        "verify_title":       "Verify your email",
        "verify_instruction": "Enter the 6-digit code we sent to your email address.",
        "verify_code_label":  "Verification code",
        "verify_btn":         "Verify my email",
        "resend_hint":        "Didn't receive the email?",
        "resend_btn":         "Resend verification email",
        "days_left_note":     "Your account will be deleted if you don't verify within {n} day(s).",
        "err_invalid_code":   "Incorrect code. Check your email or request a new one.",
        "err_no_code":        "Please enter the verification code.",
        "err_token_invalid":  "The link is not valid or has already been used.",
        "ok_verified":        "Email verified! Your account is now active.",
        "ok_resent":          "We've sent you a new verification email.",
        "err_resend":         "Could not send the email. Please try again later.",
        "already_verified":   "Your email is already verified.",
        # Banner (in base.html)
        "banner_verify":      "Please verify your email to activate your account.",
        "banner_verify_link": "Verify now",
        "banner_resend":      "Resend email",
    },
}


# ---------------------------------------------------------------------------
# URL helpers
# ---------------------------------------------------------------------------

def _gallery_url(lang):
    return url_for("main.gallery_es") if lang == "es" else url_for("main.gallery_en")

def _login_url(lang):
    return url_for("auth.login_es") if lang == "es" else url_for("auth.login_en")

def _forgot_password_url(lang):
    return url_for("auth.forgot_password_es") if lang == "es" else url_for("auth.forgot_password_en")

def _register_url(lang):
    return url_for("auth.register_es") if lang == "es" else url_for("auth.register_en")

def _register_profile_url(lang):
    return url_for("auth.register_profile_es") if lang == "es" else url_for("auth.register_profile_en")

def _membership_url(lang):
    return url_for("membership.membership_es") if lang == "es" else url_for("membership.membership_en")

def _account_url(lang):
    return url_for("account.my_account_es") if lang == "es" else url_for("account.my_account_en")

def _verify_page_url(lang):
    return url_for("auth.verify_page_es") if lang == "es" else url_for("auth.verify_page_en")

def _resend_url(lang):
    return url_for("auth.resend_verification_es") if lang == "es" else url_for("auth.resend_verification_en")


# ---------------------------------------------------------------------------
# Step 1 — choose plan
# ---------------------------------------------------------------------------

def _handle_register_step1(lang):
    ui = UI[lang]
    alt_lang_url = _register_url("en" if lang == "es" else "es")

    if current_user.is_authenticated:
        return redirect(_gallery_url(lang))

    if request.method == "POST":
        intent = request.form.get("intent", "free")
        if intent not in ("free", "gold"):
            intent = "free"
        session["signup_intent"] = intent
        session["signup_lang"]   = lang
        return redirect(_register_profile_url(lang))

    return render_template(
        "auth/register_step1.html",
        lang=lang,
        ui=ui,
        alt_lang_url=alt_lang_url,
        login_url=_login_url(lang),
        founder_active=_founder_active(),
        founder_claimed=_gold_count(),
        founder_left=max(0, FOUNDER_CUTOFF_COUNT - _gold_count()),
        founder_total=FOUNDER_CUTOFF_COUNT,
    )


@auth.route("/es/cuenta/registro", methods=["GET", "POST"])
def register_es():
    return _handle_register_step1("es")


@auth.route("/en/account/register", methods=["GET", "POST"])
def register_en():
    return _handle_register_step1("en")


# ---------------------------------------------------------------------------
# Step 2 — account data + profile
# ---------------------------------------------------------------------------

def _handle_register_step2(lang):
    ui = UI[lang]
    alt_lang_url = _register_profile_url("en" if lang == "es" else "es")

    if current_user.is_authenticated:
        return redirect(_gallery_url(lang))

    # If someone lands here without going through step 1, default to free
    intent = session.get("signup_intent", "free")

    if request.method == "POST":
        email        = request.form.get("email", "").strip().lower()
        password     = request.form.get("password", "").strip()
        display_name = request.form.get("display_name", "").strip() or None
        bio          = request.form.get("bio", "").strip() or None

        # Validation
        if not email or not password:
            flash(ui["err_fields"], "error")
        elif len(password) < 8:
            flash(ui["err_pw_short"], "error")
        elif User.query.filter_by(email=email).first():
            flash(ui["err_email"], "error")
        else:
            # Always create as free — webhook upgrades to gold after payment
            user = User(
                email=email,
                role="free",
                is_active=True,
                display_name=display_name,
                bio_es=bio if lang == "es" else None,
                bio_en=bio if lang == "en" else None,
            )
            user.set_password(password)
            db.session.add(user)
            db.session.flush()   # get user.id before avatar upload

            # Optional avatar
            avatar_file = request.files.get("avatar_file")
            if avatar_file and avatar_file.filename:
                mf, err = save_upload_file(avatar_file, allowed_types={"image"},
                                           uploader_id=user.id)
                if mf:
                    user.avatar_media_id = mf.id
                else:
                    flash(f"{ui['err_avatar']} {err or ''}", "error")

            db.session.commit()
            login_user(user)

            # Send verification email immediately. Account creation still succeeds if SMTP is down.
            email_ok, _email_err = send_verification_email(user, lang)
            send_internal_signup_notification(user, intent, lang)

            # Clear signup session keys
            session.pop("signup_intent", None)
            session.pop("signup_lang", None)

            if intent == "gold":
                if not email_ok:
                    flash(ui["err_verify_email_send"], "error")
                flash(ui["ok_registered_gold"], "success")
                return redirect(_membership_url(lang))
            else:
                if not email_ok:
                    flash(ui["err_verify_email_send"], "error")
                flash(ui["ok_registered_free"], "success")
                return redirect(_account_url(lang))

    return render_template(
        "auth/register_step2.html",
        lang=lang,
        ui=ui,
        alt_lang_url=alt_lang_url,
        intent=intent,
        login_url=_login_url(lang),
        back_url=_register_url(lang),
    )


@auth.route("/es/cuenta/registro/perfil", methods=["GET", "POST"])
def register_profile_es():
    return _handle_register_step2("es")


@auth.route("/en/account/register/profile", methods=["GET", "POST"])
def register_profile_en():
    return _handle_register_step2("en")


# ---------------------------------------------------------------------------
# Email verification — code entry page
# ---------------------------------------------------------------------------

def _handle_verify_page(lang):
    ui = UI[lang]

    if not current_user.is_authenticated:
        return redirect(_login_url(lang))

    if current_user.email_verified:
        flash(ui["already_verified"], "info")
        return redirect(_account_url(lang))

    # Calculate days remaining before account deletion
    days_left = None
    if current_user.email_verify_sent_at:
        elapsed = datetime.utcnow() - current_user.email_verify_sent_at
        remaining = timedelta(days=7) - elapsed
        days_left = max(0, remaining.days + (1 if remaining.seconds > 0 else 0))

    if request.method == "POST":
        code = request.form.get("code", "").strip()
        if not code:
            flash(ui["err_no_code"], "error")
        elif code == current_user.email_verify_code:
            current_user.email_verified       = True
            current_user.email_verify_code    = None
            current_user.email_verify_token   = None
            db.session.commit()
            flash(ui["ok_verified"], "success")
            return redirect(_account_url(lang))
        else:
            flash(ui["err_invalid_code"], "error")

    return render_template(
        "auth/verify.html",
        lang=lang,
        ui=ui,
        alt_lang_url=_verify_page_url("en" if lang == "es" else "es"),
        resend_url=_resend_url(lang),
        days_left=days_left,
    )


@auth.route("/es/cuenta/verificar", methods=["GET", "POST"])
def verify_page_es():
    return _handle_verify_page("es")


@auth.route("/en/account/verify", methods=["GET", "POST"])
def verify_page_en():
    return _handle_verify_page("en")


# ---------------------------------------------------------------------------
# Email verification — magic link (token in URL)
# ---------------------------------------------------------------------------

def _handle_verify_link(lang, token):
    ui = UI[lang]

    # Find user by token (no login required — token proves ownership)
    user = User.query.filter_by(email_verify_token=token).first()
    if not user:
        flash(ui["err_token_invalid"], "error")
        dest = _login_url(lang)
        return redirect(dest)

    if not user.email_verified:
        user.email_verified     = True
        user.email_verify_code  = None
        user.email_verify_token = None
        db.session.commit()

    # Log the user in if they aren't already
    if not current_user.is_authenticated:
        login_user(user, remember=True)

    flash(ui["ok_verified"], "success")
    return redirect(_account_url(lang))


@auth.route("/es/cuenta/verificar/<token>")
def verify_link_es(token):
    return _handle_verify_link("es", token)


@auth.route("/en/account/verify/<token>")
def verify_link_en(token):
    return _handle_verify_link("en", token)


# ---------------------------------------------------------------------------
# Email verification — resend
# ---------------------------------------------------------------------------

def _handle_resend(lang):
    ui = UI[lang]

    if not current_user.is_authenticated:
        return redirect(_login_url(lang))

    if current_user.email_verified:
        flash(ui["already_verified"], "info")
        return redirect(_account_url(lang))

    ok, err = send_verification_email(current_user, lang)
    if ok:
        flash(ui["ok_resent"], "success")
    else:
        flash(ui["err_resend"], "error")

    return redirect(request.referrer or _account_url(lang))


@auth.route("/es/cuenta/reenviar-verificacion", methods=["POST"])
def resend_verification_es():
    return _handle_resend("es")


@auth.route("/en/account/resend-verification", methods=["POST"])
def resend_verification_en():
    return _handle_resend("en")


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

def _handle_login(lang):
    ui = UI[lang]
    alt_lang_url = _login_url("en" if lang == "es" else "es")

    if current_user.is_authenticated:
        return redirect(_gallery_url(lang))

    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        if not email or not password:
            flash(ui["err_fields"], "error")
        else:
            user = User.query.filter_by(email=email).first()
            if user and not user.is_active:
                flash(ui["err_inactive"], "error")
            elif user and user.check_password(password):
                login_user(user, remember=True)
                flash(ui["ok_login"], "success")
                next_url = request.args.get("next")
                return redirect(next_url or _gallery_url(lang))
            else:
                flash(ui["err_credentials"], "error")

    return render_template(
        "auth/login.html",
        lang=lang,
        ui=ui,
        alt_lang_url=alt_lang_url,
        register_url=_register_url(lang),
        forgot_password_url=_forgot_password_url(lang),
    )


@auth.route("/es/cuenta/entrar", methods=["GET", "POST"])
def login_es():
    return _handle_login("es")


@auth.route("/en/account/login", methods=["GET", "POST"])
def login_en():
    return _handle_login("en")


# ---------------------------------------------------------------------------
# Password reset
# ---------------------------------------------------------------------------

def _handle_forgot_password(lang):
    ui = UI[lang]
    alt_lang_url = _forgot_password_url("en" if lang == "es" else "es")

    if current_user.is_authenticated:
        return redirect(_gallery_url(lang))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        if email:
            user = User.query.filter_by(email=email, is_active=True).first()
            if user:
                send_password_reset_email(user, lang)
        flash(ui["forgot_sent"], "info")
        return redirect(_login_url(lang))

    return render_template(
        "auth/forgot_password.html",
        lang=lang,
        ui=ui,
        alt_lang_url=alt_lang_url,
        login_url=_login_url(lang),
    )


def _handle_reset_password(lang, token):
    ui = UI[lang]
    alt_lang_url = (
        url_for("auth.reset_password_en", token=token)
        if lang == "es" else url_for("auth.reset_password_es", token=token)
    )
    user = User.query.filter_by(password_reset_token=token).first()
    expired = True
    if user and user.password_reset_sent_at:
        expired = datetime.utcnow() - user.password_reset_sent_at > timedelta(hours=1)

    if not user or expired:
        flash(ui["reset_invalid"], "error")
        return redirect(_forgot_password_url(lang))

    if request.method == "POST":
        password = request.form.get("password", "").strip()
        if len(password) < 8:
            flash(ui["err_pw_short"], "error")
        else:
            user.set_password(password)
            user.password_reset_token = None
            user.password_reset_sent_at = None
            db.session.commit()
            flash(ui["reset_ok"], "success")
            return redirect(_login_url(lang))

    return render_template(
        "auth/reset_password.html",
        lang=lang,
        ui=ui,
        alt_lang_url=alt_lang_url,
    )


@auth.route("/es/cuenta/recuperar", methods=["GET", "POST"])
def forgot_password_es():
    return _handle_forgot_password("es")


@auth.route("/en/account/forgot-password", methods=["GET", "POST"])
def forgot_password_en():
    return _handle_forgot_password("en")


@auth.route("/es/cuenta/restablecer/<token>", methods=["GET", "POST"])
def reset_password_es(token):
    return _handle_reset_password("es", token)


@auth.route("/en/account/reset-password/<token>", methods=["GET", "POST"])
def reset_password_en(token):
    return _handle_reset_password("en", token)


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------

@auth.route("/salir")
@login_required
def logout():
    lang = request.args.get("lang", "es")
    ui = UI.get(lang, UI["es"])
    logout_user()
    flash(ui["ok_logout"], "info")
    return redirect(_gallery_url(lang))

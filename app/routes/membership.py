"""
app/routes/membership.py

Membership pages, Stripe Checkout, Stripe Customer Portal, and webhook handler.
"""
import os
import stripe
from datetime import datetime, timezone

from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, abort, current_app, jsonify,
)
from flask_login import login_required, current_user

from app import db
from app.models import AdComment, User
from app.email import (
    send_gold_welcome_email,
    send_internal_gold_activation_notification,
    send_refund_notice_email,
)

membership_bp = Blueprint("membership", __name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Founder pricing is reserved for the first Gold subscribers only.
FOUNDER_CUTOFF_COUNT = 1000
DEFAULT_MEMBERSHIP_HERO_IMAGE_URL = (
    "https://res.cloudinary.com/dslebikvo/image/upload/v1783213234/"
    "adcritic/images/ibfubiameveuxywqkcxa.jpg"
)
DEFAULT_FOUNDER_SHIELD_IMAGE_URL = (
    "https://res.cloudinary.com/dslebikvo/image/upload/v1783215415/"
    "adcritic/images/wmh7gbugyszgpzx9mfub.png"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _configure_stripe():
    stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")


def _price_ids():
    """Return dict of plan key → Stripe Price ID (from env vars)."""
    return {
        "monthly":         os.environ.get("STRIPE_PRICE_ID_MONTHLY", ""),
        "yearly":          os.environ.get("STRIPE_PRICE_ID_YEARLY", ""),
        "monthly_founder": os.environ.get("STRIPE_PRICE_ID_MONTHLY_FOUNDER", ""),
        "yearly_founder":  os.environ.get("STRIPE_PRICE_ID_YEARLY_FOUNDER", ""),
    }


def _membership_asset_urls():
    """Return Cloudinary-backed membership assets, with local fallbacks for dev."""
    return {
        "hero": os.environ.get("MEMBERSHIP_HERO_IMAGE_URL")
        or DEFAULT_MEMBERSHIP_HERO_IMAGE_URL,
        "shield": os.environ.get("FOUNDER_SHIELD_IMAGE_URL")
        or DEFAULT_FOUNDER_SHIELD_IMAGE_URL,
    }


def _using_test_billing():
    """True when billing config is test/local, so demo users should not consume Founder spots."""
    keys = (
        os.environ.get("STRIPE_SECRET_KEY", ""),
        os.environ.get("STRIPE_PUBLISHABLE_KEY", ""),
    )
    return not all(keys) or any("_test_" in key for key in keys)


def _founder_claimed_count():
    override = os.environ.get("FOUNDER_CLAIMED_COUNT")
    if override is not None:
        try:
            return max(0, int(override))
        except ValueError:
            return 0
    if _using_test_billing():
        return 0
    return User.query.filter(
        User.role == "gold",
        User.stripe_subscription_id.isnot(None),
    ).count()


def _founder_active():
    """True while founder pricing spots remain."""
    return _founder_claimed_count() < FOUNDER_CUTOFF_COUNT


def _gold_count():
    """Number of Founder spots already claimed for display."""
    return _founder_claimed_count()


def _plan_label(price_id, lang):
    """Human-readable plan name for a given Price ID."""
    ids = _price_ids()
    labels = {
        ids["monthly"]:         {"es": "Mensual estándar",  "en": "Monthly standard"},
        ids["yearly"]:          {"es": "Anual estándar",    "en": "Annual standard"},
        ids["monthly_founder"]: {"es": "Mensual fundador",  "en": "Monthly founder"},
        ids["yearly_founder"]:  {"es": "Anual fundador",    "en": "Annual founder"},
    }
    entry = labels.get(price_id or "")
    return entry[lang] if entry else (price_id or "Gold")


def _get_subscription_info(user):
    """
    Fetch current subscription details from Stripe.
    Returns dict with keys: status, renews_at (datetime), price_id, cancel_at_period_end.
    Returns None if the user has no subscription.

    NOTE: Stripe SDK 15.x with billing_mode=flexible moves current_period_end
    from the subscription root to sub["items"]["data"][0]["current_period_end"].
    We check both locations for forward-compatibility.
    """
    if not user.stripe_subscription_id:
        return None
    _configure_stripe()
    try:
        sub   = stripe.Subscription.retrieve(user.stripe_subscription_id)
        items = sub["items"]["data"] if "items" in sub and sub["items"]["data"] else []

        # current_period_end: root level (legacy) or item level (billing_mode=flexible)
        ts = None
        try:
            ts = sub["current_period_end"]
        except KeyError:
            pass
        if ts is None and items:
            try:
                ts = items[0]["current_period_end"]
            except (KeyError, IndexError):
                pass

        period_end = datetime.fromtimestamp(ts, tz=timezone.utc) if ts else None
        price_id   = items[0]["price"]["id"] if items else None

        return {
            "status":               sub["status"],
            "renews_at":            period_end,
            "price_id":             price_id,
            "cancel_at_period_end": _sg(sub, "cancel_at_period_end") or False,
        }
    except (stripe.StripeError, Exception):
        return None


def _stripe_id(value):
    """Return the id from a Stripe id string or expanded Stripe object."""
    if not value:
        return None
    if isinstance(value, str):
        return value
    return _sg(value, "id")


def _activate_gold_membership(user):
    was_gold = user.role == "gold"
    had_prior_critiques = AdComment.query.filter_by(user_id=user.id).first() is not None
    user.role = "gold"
    if not was_gold:
        user.gold_started_at = datetime.utcnow()
        user.gold_intro_critiques_used = User.GOLD_INTRO_CRITIQUE_LIMIT if had_prior_critiques else 0
    elif user.gold_started_at is None:
        user.gold_started_at = datetime.utcnow()
        if had_prior_critiques:
            user.gold_intro_critiques_used = User.GOLD_INTRO_CRITIQUE_LIMIT


# ---------------------------------------------------------------------------
# UI strings
# ---------------------------------------------------------------------------

UI = {
    "es": {
        "page_title":          "Membresía Gold",
        "hero_subtitle":       "Desbloquea análisis completos, valora trabajos de mérito publicitario y publica tus críticas junto a una comunidad de profesionales de la industria.",
        "plan_monthly":        "Mensual",
        "plan_yearly":         "Anual",
        "plan_yearly_save":    "Ahorra 25 %",
        "plan_founder_badge":  "Miembro fundador",
        "founder_note":        "Precio especial para los primeros {n} miembros.",
        "founder_expired":     "",
        "features": [
            "Análisis completo de todos los anuncios",
            "Publica críticas",
            "Acceso a artículos exclusivos Gold",
            "Apoya la crítica publicitaria independiente",
        ],
        "btn_subscribe":       "Suscribirme",
        "btn_manage":          "Gestionar mi suscripción",
        "already_gold_title":  "Ya eres miembro Gold",
        "already_gold_body":   "Disfruta tu acceso completo a las críticas y los artículos exclusivos.",
        "already_gold_link":   "Ir a críticas",
        "login_required":      "Inicia sesión para suscribirte.",
        "period_monthly":      "/ mes",
        "period_yearly":       "/ año",
        # Success page
        "success_title":       "¡Bienvenido a Gold!",
        "success_body":        "Tu membresía está activa. Ya tienes acceso completo a las críticas.",
        "success_cta_catalog": "Explorar críticas",
        "success_cta_account": "Ver mi cuenta",
        # Account section
        "section_membership":  "Tu membresía",
        "label_plan":          "Plan",
        "label_renews":        "Próxima renovación",
        "label_cancels":       "Cancela el",
        "btn_portal":          "Gestionar mi suscripción",
        "portal_note":         "Cambia de plan, cancela o actualiza tu método de pago.",
        "no_subscription":     "No tienes una suscripción activa.",
        "upgrade_link":        "Ver planes",
    },
    "en": {
        "page_title":          "Gold Membership",
        "hero_subtitle":       "Unlock full analysis, recognize work of advertising merit, and publish your critiques alongside a community of industry professionals.",
        "plan_monthly":        "Monthly",
        "plan_yearly":         "Annual",
        "plan_yearly_save":    "Save 25%",
        "plan_founder_badge":  "Founder member",
        "founder_note":        "Special price for the first {n} members.",
        "founder_expired":     "",
        "features": [
            "Full analysis of every ad",
            "Post critiques",
            "Access to Gold-exclusive articles",
            "Support independent ad criticism",
        ],
        "btn_subscribe":       "Subscribe",
        "btn_manage":          "Manage my subscription",
        "already_gold_title":  "You're already a Gold member",
        "already_gold_body":   "Enjoy your full access to critiques and exclusive articles.",
        "already_gold_link":   "Go to critiques",
        "login_required":      "Sign in to subscribe.",
        "period_monthly":      "/ month",
        "period_yearly":       "/ year",
        # Success page
        "success_title":       "Welcome to Gold!",
        "success_body":        "Your membership is active. You now have full access to critiques.",
        "success_cta_catalog": "Explore critiques",
        "success_cta_account": "View my account",
        # Account section
        "section_membership":  "Your membership",
        "label_plan":          "Plan",
        "label_renews":        "Next renewal",
        "label_cancels":       "Cancels on",
        "btn_portal":          "Manage my subscription",
        "portal_note":         "Change plan, cancel, or update your payment method.",
        "no_subscription":     "You don't have an active subscription.",
        "upgrade_link":        "View plans",
    },
}


# ---------------------------------------------------------------------------
# Membership pages
# ---------------------------------------------------------------------------

def _handle_membership_page(lang):
    ui = UI[lang]
    founder = _founder_active()
    ids = _price_ids()

    # Pick which price IDs to show
    if founder:
        monthly_price_id = ids["monthly_founder"]
        yearly_price_id  = ids["yearly_founder"]
        monthly_amount   = "6.99"
        yearly_amount    = "69.99"
    else:
        monthly_price_id = ids["monthly"]
        yearly_price_id  = ids["yearly"]
        monthly_amount   = "9.99"
        yearly_amount    = "89.99"

    founder_claimed = _gold_count()
    left = max(0, FOUNDER_CUTOFF_COUNT - founder_claimed)

    stripe_public_key = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")
    checkout_url = url_for(f"membership.membership_checkout_{lang}")
    alt_lang_url = url_for("membership.membership_en") if lang == "es" else url_for("membership.membership_es")
    membership_assets = _membership_asset_urls()

    return render_template(
        f"{lang}/membership.html",
        lang=lang,
        ui=ui,
        alt_lang_url=alt_lang_url,
        founder=founder,
        left=left,
        founder_claimed=founder_claimed,
        founder_total=FOUNDER_CUTOFF_COUNT,
        monthly_price_id=monthly_price_id,
        yearly_price_id=yearly_price_id,
        monthly_amount=monthly_amount,
        yearly_amount=yearly_amount,
        stripe_public_key=stripe_public_key,
        checkout_url=checkout_url,
        membership_hero_url=membership_assets["hero"],
        founder_shield_url=membership_assets["shield"],
    )


@membership_bp.route("/es/membresia/")
def membership_es():
    return _handle_membership_page("es")


@membership_bp.route("/en/membership/")
def membership_en():
    return _handle_membership_page("en")


# ---------------------------------------------------------------------------
# Stripe Embedded Checkout — create session, return client_secret as JSON
# ---------------------------------------------------------------------------

def _handle_checkout(lang):
    """
    Called via fetch() from the membership page JS.
    Returns JSON { clientSecret } for Stripe Embedded Checkout,
    or JSON { error } on failure.
    """
    if not current_user.is_authenticated:
        return jsonify({"error": "not_authenticated"}), 401

    # Accept both JSON body (fetch) and form data (fallback)
    data = request.get_json(silent=True) or {}
    plan = data.get("plan") or request.form.get("plan", "monthly")

    founder  = _founder_active()
    ids      = _price_ids()
    price_id = (ids["yearly_founder"]  if founder else ids["yearly"])  \
               if plan == "yearly" else \
               (ids["monthly_founder"] if founder else ids["monthly"])

    if not price_id:
        return jsonify({"error": "price_not_found"}), 400

    _configure_stripe()

    return_url = url_for(
        f"membership.membership_success_{lang}", _external=True,
    ) + "?session_id={CHECKOUT_SESSION_ID}"

    try:
        kwargs = dict(
            ui_mode="embedded_page",
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            return_url=return_url,
            client_reference_id=str(current_user.id),
            customer_email=current_user.email,
            allow_promotion_codes=True,
            metadata={"user_id": str(current_user.id), "lang": lang},
        )
        if current_user.stripe_customer_id:
            kwargs["customer"] = current_user.stripe_customer_id
            del kwargs["customer_email"]

        session = stripe.checkout.Session.create(**kwargs)
        return jsonify({"clientSecret": session.client_secret}), 200

    except stripe.StripeError as e:
        current_app.logger.error(f"Stripe embedded checkout error: {e}")
        return jsonify({"error": str(e)}), 500


@membership_bp.route("/es/membresia/checkout/", methods=["POST"])
def membership_checkout_es():
    return _handle_checkout("es")


@membership_bp.route("/en/membership/checkout/", methods=["POST"])
def membership_checkout_en():
    return _handle_checkout("en")


# ---------------------------------------------------------------------------
# Success page (after Stripe redirects back)
# ---------------------------------------------------------------------------

def _handle_success(lang):
    ui = UI[lang]
    session_id = request.args.get("session_id", "").strip()
    if session_id:
        _sync_checkout_session_for_current_user(session_id)

    return render_template(
        f"{lang}/membership_success.html",
        lang=lang,
        ui=ui,
    )


@membership_bp.route("/es/membresia/bienvenido/")
def membership_success_es():
    return _handle_success("es")


@membership_bp.route("/en/membership/welcome/")
def membership_success_en():
    return _handle_success("en")


# ---------------------------------------------------------------------------
# Stripe Customer Portal
# ---------------------------------------------------------------------------

def _handle_portal(lang):
    if not current_user.is_authenticated:
        return redirect(url_for(f"auth.login_{lang}"))
    if not current_user.stripe_customer_id:
        flash("No tienes una suscripción activa." if lang == "es"
              else "You don't have an active subscription.", "info")
        return redirect(url_for(f"membership.membership_{lang}"))

    _configure_stripe()
    return_url = url_for(f"account.my_account_{lang}", _external=True)

    try:
        portal = stripe.billing_portal.Session.create(
            customer=current_user.stripe_customer_id,
            return_url=return_url,
        )
        return redirect(portal.url, code=303)
    except stripe.StripeError as e:
        current_app.logger.error(f"Stripe portal error: {e}")
        flash("Error al abrir el portal de Stripe. Intenta de nuevo.", "error")
        return redirect(url_for(f"account.my_account_{lang}"))


@membership_bp.route("/es/membresia/portal/")
@login_required
def membership_portal_es():
    return _handle_portal("es")


@membership_bp.route("/en/membership/portal/")
@login_required
def membership_portal_en():
    return _handle_portal("en")


# ---------------------------------------------------------------------------
# Stripe Webhook
# ---------------------------------------------------------------------------

@membership_bp.route("/webhooks/stripe", methods=["POST"])
@membership_bp.route("/stripe/webhook", methods=["POST"])
def stripe_webhook():
    payload    = request.get_data()          # raw bytes — required for sig check
    sig_header = request.headers.get("Stripe-Signature", "")
    webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

    _configure_stripe()

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except stripe.SignatureVerificationError:
        current_app.logger.warning("Stripe webhook: invalid signature")
        abort(400)
    except Exception as e:
        current_app.logger.error(f"Stripe webhook parse error: {e}")
        abort(400)

    etype = event["type"]
    data  = event["data"]["object"]

    # ── checkout.session.completed → activate Gold ───────────────────────────
    if etype == "checkout.session.completed":
        _handle_checkout_completed(data)

    # ── invoice.paid → ensure Gold is active on renewals ────────────────────
    elif etype == "invoice.paid":
        _handle_invoice_paid(data)

    # ── customer.subscription.deleted → downgrade to free ───────────────────
    elif etype == "customer.subscription.deleted":
        _handle_subscription_deleted(data)

    # ── invoice.payment_failed → log (Stripe will retry; sub deletion handles final downgrade) ──
    elif etype == "invoice.payment_failed":
        customer_id = _sg(data, "customer")
        current_app.logger.warning(
            f"Stripe invoice payment failed for customer {customer_id}"
        )

    # ── charge.refunded → neutral notice email (does not change membership) ──
    elif etype == "charge.refunded":
        _handle_charge_refunded(data)

    return {"status": "ok"}, 200


def _sg(obj, key, default=None):
    """
    Safe getter for Stripe SDK 15.x objects (StripeObject no longer has .get()).
    Works with both StripeObject (attribute access) and plain dicts.
    """
    try:
        val = obj[key]
        return val if val is not None else default
    except (KeyError, TypeError, AttributeError):
        return default


def _sync_checkout_session_for_current_user(session_id):
    """
    Fallback for local/test flows where Stripe cannot reach the webhook.
    The webhook remains the main source of truth, but the return page can safely
    activate Gold after Stripe confirms this user's Checkout Session completed.
    """
    if not current_user.is_authenticated:
        return False

    _configure_stripe()
    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except stripe.StripeError as e:
        current_app.logger.error(f"Stripe success sync error: {e}")
        return False

    if _sg(session, "status") != "complete":
        current_app.logger.info(
            f"Stripe success sync skipped: incomplete session {session_id}"
        )
        return False

    ref = _sg(session, "client_reference_id")
    customer_id = _sg(session, "customer")
    cd = _sg(session, "customer_details")
    email = (_sg(cd, "email") if cd else None) or _sg(session, "customer_email")

    belongs_to_current_user = (
        (ref and str(ref) == str(current_user.id))
        or (email and email.lower() == current_user.email.lower())
        or (
            customer_id
            and current_user.stripe_customer_id
            and customer_id == current_user.stripe_customer_id
        )
    )
    if not belongs_to_current_user:
        current_app.logger.warning(
            f"Stripe success sync rejected: session {session_id} does not match "
            f"user {current_user.id}"
        )
        return False

    _handle_checkout_completed(session)
    return True


def _find_user_for_webhook(data, *, customer_id_key="customer",
                            ref_key="client_reference_id"):
    """
    Resolve a User from a Stripe webhook payload.
    Priority: client_reference_id (user.id) → stripe_customer_id → email.
    """
    # 1. client_reference_id = our user.id (set at checkout creation)
    ref = _sg(data, ref_key)
    if ref and str(ref).isdigit():
        user = User.query.get(int(ref))
        if user:
            return user

    # 2. stripe_customer_id already stored
    customer_id = _sg(data, customer_id_key)
    if customer_id:
        user = User.query.filter_by(stripe_customer_id=customer_id).first()
        if user:
            return user

    # 3. email (only present on checkout.session)
    cd    = _sg(data, "customer_details")
    email = (_sg(cd, "email") if cd else None) or _sg(data, "customer_email")
    if email:
        return User.query.filter_by(email=email).first()

    return None


def _handle_checkout_completed(session):
    user = _find_user_for_webhook(session)
    if not user:
        current_app.logger.error(
            f"Webhook checkout.session.completed: could not find user. "
            f"ref={_sg(session, 'client_reference_id')} "
            f"customer={_sg(session, 'customer')}"
        )
        return

    subscription_id = _stripe_id(_sg(session, "subscription"))
    customer_id     = _stripe_id(_sg(session, "customer"))

    # Fetch price_id from the subscription
    price_id = None
    if subscription_id:
        try:
            sub   = stripe.Subscription.retrieve(subscription_id)
            items = sub["items"]["data"] if "items" in sub else []
            if items:
                price_id = items[0]["price"]["id"]
        except stripe.StripeError as e:
            current_app.logger.error(f"Could not retrieve subscription: {e}")

    was_gold = user.role == "gold"

    _activate_gold_membership(user)
    user.stripe_customer_id     = customer_id or user.stripe_customer_id
    user.stripe_subscription_id = subscription_id or user.stripe_subscription_id
    user.stripe_price_id        = price_id or user.stripe_price_id
    # Payment proves email ownership — auto-verify
    user.email_verified         = True
    user.email_verify_code      = None
    user.email_verify_token     = None
    db.session.commit()

    current_app.logger.info(
        f"Gold activated: user {user.id} ({user.email}), "
        f"sub={subscription_id}, price={price_id}"
    )

    if not was_gold:
        metadata = _sg(session, "metadata") or {}
        lang = _sg(metadata, "lang") or "es"
        send_gold_welcome_email(user, lang)
        send_internal_gold_activation_notification(
            user,
            price_id=price_id,
            subscription_id=subscription_id,
        )


def _handle_invoice_paid(invoice):
    """On successful renewal, ensure the user is still Gold."""
    customer_id     = _sg(invoice, "customer")
    subscription_id = _sg(invoice, "subscription")
    if not customer_id:
        return

    user = User.query.filter_by(stripe_customer_id=customer_id).first()
    if not user:
        return

    if user.role != "gold":
        _activate_gold_membership(user)
        current_app.logger.info(
            f"Gold restored on renewal: user {user.id} ({user.email})"
        )
    elif user.gold_started_at is None:
        _activate_gold_membership(user)

    if subscription_id:
        user.stripe_subscription_id = subscription_id

    db.session.commit()


def _handle_subscription_deleted(subscription):
    """When a subscription is fully cancelled/expired, downgrade to free."""
    customer_id     = _sg(subscription, "customer")
    subscription_id = _sg(subscription, "id")

    user = None
    if subscription_id:
        user = User.query.filter_by(stripe_subscription_id=subscription_id).first()
    if not user and customer_id:
        user = User.query.filter_by(stripe_customer_id=customer_id).first()

    if not user:
        current_app.logger.warning(
            f"Webhook subscription.deleted: no user found for "
            f"sub={subscription_id} customer={customer_id}"
        )
        return

    user.role                   = "free"
    user.stripe_subscription_id = None
    user.stripe_price_id        = None
    db.session.commit()


def _handle_charge_refunded(charge):
    """
    Send a neutral notice when a charge is refunded. Refunds don't change
    membership by themselves — Stripe treats refund and subscription
    cancellation as separate actions, so downgrade happens only via
    customer.subscription.deleted.
    """
    customer_id = _sg(charge, "customer")
    if not customer_id:
        return

    user = User.query.filter_by(stripe_customer_id=customer_id).first()
    if not user:
        current_app.logger.warning(
            f"Webhook charge.refunded: no user found for customer {customer_id}"
        )
        return

    send_refund_notice_email(user)

    current_app.logger.info(
        f"Gold cancelled → free: user {user.id} ({user.email})"
    )

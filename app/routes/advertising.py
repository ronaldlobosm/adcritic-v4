"""
Advertising routes:
  - Public click-tracking redirect    /ads/click/<id>
  - Admin: advertisers CRUD           /admin/publicidad/clientes/
  - Admin: banner ads CRUD            /admin/publicidad/anuncios/
"""
from functools import wraps
from datetime import datetime, date
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, abort,
)
from flask_login import current_user, login_required
from app import db
from app.models import Advertiser, AdCampaign, AdZone, BannerAd
from app.routes.admin import ADMIN_UI

advertising_bp = Blueprint("advertising", __name__)

# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_staff:
            abort(403)
        return f(*args, **kwargs)
    return decorated


def _only_admin():
    """Abort 403 if current user is not admin."""
    if not current_user.is_authenticated or current_user.role != "admin":
        abort(403)


# ---------------------------------------------------------------------------
# Admin UI strings
# ---------------------------------------------------------------------------

ADV_UI = {
    "es": {
        "page_advertisers":     "Clientes publicitarios",
        "page_new_advertiser":  "Nuevo cliente",
        "page_edit_advertiser": "Editar cliente",
        "page_banners":         "Anuncios / Banners",
        "page_new_banner":      "Nuevo anuncio",
        "page_edit_banner":     "Editar anuncio",
        "page_campaigns":       "Campañas",
        "page_new_campaign":    "Nueva campaña",
        "page_edit_campaign":   "Editar campaña",
        "btn_new_campaign":     "+ Nueva campaña",
        "label_campaign_name":  "Nombre de campaña",
        "label_ad_name":        "Nombre del anuncio",
        "label_campaign":       "Campaña",
        "no_campaign":          "Sin campaña",
        "empty_campaigns":      "No hay campañas registradas.",
        "th_company":           "Empresa",
        "th_contact":           "Contacto",
        "th_email":             "Email",
        "th_active":            "Activo",
        "th_actions":           "Acciones",
        "th_zone":              "Zona",
        "th_client":            "Cliente",
        "th_type":              "Tipo",
        "th_impressions":       "Impresiones",
        "th_clicks":            "Clics",
        "th_dates":             "Vigencia",
        "btn_new_client":       "+ Nuevo cliente",
        "btn_new_banner":       "+ Nuevo anuncio",
        "btn_edit":             "Editar",
        "btn_delete":           "Eliminar",
        "btn_toggle_on":        "Activar",
        "btn_toggle_off":       "Pausar",
        "btn_save":             "Guardar",
        "btn_cancel":           "Cancelar",
        "label_company":        "Empresa",
        "label_contact_name":   "Nombre de contacto",
        "label_contact_email":  "Email de contacto",
        "label_active":         "Activo",
        "label_zone":           "Zona publicitaria",
        "label_client":         "Cliente (opcional)",
        "label_type":           "Tipo de contenido",
        "label_content_image":  "URL de imagen",
        "label_content_video":  "URL de video",
        "label_content_embed":    "Código HTML / JS",
        "label_click_url":        "URL de destino (clic)",
        "label_start_date":       "Fecha de inicio",
        "label_end_date":         "Fecha de fin",
        "label_category":         "Categoría de campaña",
        "label_target_countries": "Países objetivo",
        "label_blocked_countries":"Países bloqueados",
        "hint_embed":             "Este código se insertará tal cual en el HTML. Solo admin puede editarlo.",
        "hint_click_url":         "Deja vacío para anuncios embed (el código propio maneja el clic).",
        "hint_dates":             "Deja vacío para no limitar la vigencia.",
        "hint_countries":         "Códigos ISO-2 separados por comas, ej: PE,CL,CO — vacío = global.",
        "no_client":              "Sin cliente / Genérico",
        "no_category":            "Sin categoría",
        "no_dates":               "Sin límite",
        "geo_global":             "Global",
        "geo_target":             "Solo en",
        "geo_blocked":            "Bloqueado en",
        "empty_advertisers":      "No hay clientes registrados.",
        "empty_banners":          "No hay anuncios registrados.",
        "confirm_delete":         "¿Eliminar? No se puede deshacer.",
        "saved":                  "Guardado.",
        "deleted":                "Eliminado.",
        "toggled_on":             "Anuncio activado.",
        "toggled_off":            "Anuncio pausado.",
        "type_image":             "Imagen",
        "type_video":             "Video",
        "type_embed":             "Código embed",
        "filter_all_clients":     "Todos los clientes",
        "filter_all_campaigns":   "Todas las campañas",
        "filter_all_zones":       "Todas las zonas",
        "filter_all_types":       "Todos los tipos",
        "filter_all_status":      "Cualquier estado",
        "filter_active":          "Activos",
        "filter_paused":          "Pausados",
        "filter_all_geo":         "Todos los países",
        "cat_awareness":          "Branding / Awareness",
        "cat_conversion":         "Conversión",
        "cat_retargeting":        "Retargeting",
        "cat_launch":             "Lanzamiento",
        "cat_seasonal":           "Estacional",
        "cat_institutional":      "Institucional",
    },
    "en": {
        "page_advertisers":       "Advertisers",
        "page_new_advertiser":    "New advertiser",
        "page_edit_advertiser":   "Edit advertiser",
        "page_banners":           "Banner ads",
        "page_new_banner":        "New banner ad",
        "page_edit_banner":       "Edit banner ad",
        "page_campaigns":         "Campaigns",
        "page_new_campaign":      "New campaign",
        "page_edit_campaign":     "Edit campaign",
        "btn_new_campaign":       "+ New campaign",
        "label_campaign_name":    "Campaign name",
        "label_ad_name":          "Ad name",
        "label_campaign":         "Campaign",
        "no_campaign":            "No campaign",
        "empty_campaigns":        "No campaigns registered.",
        "th_company":             "Company",
        "th_contact":             "Contact",
        "th_email":               "Email",
        "th_active":              "Active",
        "th_actions":             "Actions",
        "th_zone":                "Zone",
        "th_client":              "Client",
        "th_type":                "Type",
        "th_impressions":         "Impressions",
        "th_clicks":              "Clicks",
        "th_dates":               "Period",
        "btn_new_client":         "+ New client",
        "btn_new_banner":         "+ New banner ad",
        "btn_edit":               "Edit",
        "btn_delete":             "Delete",
        "btn_toggle_on":          "Activate",
        "btn_toggle_off":         "Pause",
        "btn_save":               "Save",
        "btn_cancel":             "Cancel",
        "label_company":          "Company",
        "label_contact_name":     "Contact name",
        "label_contact_email":    "Contact email",
        "label_active":           "Active",
        "label_zone":             "Ad zone",
        "label_client":           "Client (optional)",
        "label_type":             "Content type",
        "label_content_image":    "Image URL",
        "label_content_video":    "Video URL",
        "label_content_embed":    "HTML / JS code",
        "label_click_url":        "Destination URL (click)",
        "label_start_date":       "Start date",
        "label_end_date":         "End date",
        "label_category":         "Campaign category",
        "label_target_countries": "Target countries",
        "label_blocked_countries":"Blocked countries",
        "hint_embed":             "This code will be inserted as-is into the HTML. Admin only.",
        "hint_click_url":         "Leave empty for embed ads (their own code handles clicks).",
        "hint_dates":             "Leave empty for no date limit.",
        "hint_countries":         "ISO-2 codes comma-separated, e.g. PE,CL,CO — empty = global.",
        "no_client":              "No client / Generic",
        "no_category":            "No category",
        "no_dates":               "No limit",
        "geo_global":             "Global",
        "geo_target":             "Only in",
        "geo_blocked":            "Blocked in",
        "empty_advertisers":      "No advertisers registered.",
        "empty_banners":          "No banner ads registered.",
        "confirm_delete":         "Delete? This cannot be undone.",
        "saved":                  "Saved.",
        "deleted":                "Deleted.",
        "toggled_on":             "Ad activated.",
        "toggled_off":            "Ad paused.",
        "type_image":             "Image",
        "type_video":             "Video",
        "type_embed":             "Embed code",
        "filter_all_clients":     "All clients",
        "filter_all_campaigns":   "All campaigns",
        "filter_all_zones":       "All zones",
        "filter_all_types":       "All types",
        "filter_all_status":      "Any status",
        "filter_active":          "Active",
        "filter_paused":          "Paused",
        "filter_all_geo":         "All countries",
        "cat_awareness":          "Branding / Awareness",
        "cat_conversion":         "Conversion",
        "cat_retargeting":        "Retargeting",
        "cat_launch":             "Product Launch",
        "cat_seasonal":           "Seasonal",
        "cat_institutional":      "Institutional",
    },
}

TYPE_LABELS = {
    "es": {"image": "Imagen", "video": "Video", "embed_code": "Embed"},
    "en": {"image": "Image",  "video": "Video", "embed_code": "Embed"},
}

CATEGORY_LABELS = {
    "es": {
        "awareness":     "Branding / Awareness",
        "conversion":    "Conversión",
        "retargeting":   "Retargeting",
        "launch":        "Lanzamiento",
        "seasonal":      "Estacional",
        "institutional": "Institucional",
    },
    "en": {
        "awareness":     "Branding / Awareness",
        "conversion":    "Conversion",
        "retargeting":   "Retargeting",
        "launch":        "Product Launch",
        "seasonal":      "Seasonal",
        "institutional": "Institutional",
    },
}


def _adv_ui(lang):
    return ADV_UI.get(lang, ADV_UI["es"])


def _ui(lang):
    return ADMIN_UI.get(lang, ADMIN_UI["es"])


def _lang():
    from flask import session
    return session.get("admin_lang", "es")


# ---------------------------------------------------------------------------
# Public: click tracking
# ---------------------------------------------------------------------------

@advertising_bp.route("/ads/click/<int:ad_id>")
def ad_click(ad_id):
    ad = BannerAd.query.get_or_404(ad_id)
    if ad.click_url:
        ad.clicks_count = (ad.clicks_count or 0) + 1
        db.session.commit()
        return redirect(ad.click_url)
    return redirect("/")


# ---------------------------------------------------------------------------
# Admin: Advertisers
# ---------------------------------------------------------------------------

@advertising_bp.route("/admin/publicidad/clientes/")
@login_required
@admin_required
def advertisers_list():
    _only_admin()
    lang = _lang()
    advertisers = Advertiser.query.order_by(Advertiser.company_name).all()
    return render_template(
        "admin/adv_advertisers.html",
        advertisers=advertisers,
        ui=_ui(lang), adv_ui=_adv_ui(lang), lang=lang, active="advertising",
    )


@advertising_bp.route("/admin/publicidad/clientes/nuevo", methods=["GET", "POST"])
@login_required
@admin_required
def advertiser_create():
    _only_admin()
    lang = _lang()
    adv_ui = _adv_ui(lang)
    if request.method == "POST":
        adv = Advertiser(
            company_name  = request.form.get("company_name", "").strip(),
            contact_name  = request.form.get("contact_name", "").strip() or None,
            contact_email = request.form.get("contact_email", "").strip() or None,
            is_active     = bool(request.form.get("is_active")),
        )
        db.session.add(adv)
        db.session.commit()
        flash(adv_ui["saved"], "success")
        return redirect(url_for("advertising.advertisers_list"))
    return render_template(
        "admin/adv_advertiser_form.html",
        advertiser=None, ui=_ui(lang), adv_ui=adv_ui, lang=lang, active="advertisers",
    )


@advertising_bp.route("/admin/publicidad/clientes/<int:adv_id>/editar", methods=["GET", "POST"])
@login_required
@admin_required
def advertiser_edit(adv_id):
    _only_admin()
    lang = _lang()
    adv_ui = _adv_ui(lang)
    adv = Advertiser.query.get_or_404(adv_id)
    if request.method == "POST":
        adv.company_name  = request.form.get("company_name", "").strip()
        adv.contact_name  = request.form.get("contact_name", "").strip() or None
        adv.contact_email = request.form.get("contact_email", "").strip() or None
        adv.is_active     = bool(request.form.get("is_active"))
        db.session.commit()
        flash(adv_ui["saved"], "success")
        return redirect(url_for("advertising.advertisers_list"))
    return render_template(
        "admin/adv_advertiser_form.html",
        advertiser=adv, ui=_ui(lang), adv_ui=adv_ui, lang=lang, active="advertisers",
    )


@advertising_bp.route("/admin/publicidad/clientes/<int:adv_id>/eliminar", methods=["POST"])
@login_required
@admin_required
def advertiser_delete(adv_id):
    _only_admin()
    lang = _lang()
    adv = Advertiser.query.get_or_404(adv_id)
    db.session.delete(adv)
    db.session.commit()
    flash(_adv_ui(lang)["deleted"], "success")
    return redirect(url_for("advertising.advertisers_list"))


# ---------------------------------------------------------------------------
# Admin: Banner Ads
# ---------------------------------------------------------------------------

@advertising_bp.route("/admin/publicidad/anuncios/")
@login_required
@admin_required
def banners_list():
    _only_admin()
    lang = _lang()
    advertisers = Advertiser.query.order_by(Advertiser.company_name).all()
    ungrouped   = BannerAd.query.filter_by(advertiser_id=None, campaign_id=None)\
                                .order_by(BannerAd.id).all()
    zones       = AdZone.query.order_by(AdZone.display_name).all()
    cat_labels  = CATEGORY_LABELS[lang]
    return render_template(
        "admin/adv_banners.html",
        advertisers=advertisers, ungrouped=ungrouped, zones=zones,
        ui=_ui(lang), adv_ui=_adv_ui(lang), lang=lang, active="advertising",
        type_labels=TYPE_LABELS[lang], cat_labels=cat_labels,
    )


@advertising_bp.route("/admin/publicidad/anuncios/nuevo", methods=["GET", "POST"])
@login_required
@admin_required
def banner_create():
    _only_admin()
    lang = _lang()
    adv_ui = _adv_ui(lang)
    zones       = AdZone.query.order_by(AdZone.display_name).all()
    advertisers = Advertiser.query.filter_by(is_active=True).order_by(Advertiser.company_name).all()
    campaigns   = AdCampaign.query.order_by(AdCampaign.advertiser_id, AdCampaign.name).all()
    if request.method == "POST":
        _save_banner(None, adv_ui)
        flash(adv_ui["saved"], "success")
        return redirect(url_for("advertising.banners_list"))
    return render_template(
        "admin/adv_banner_form.html",
        banner=None, zones=zones, advertisers=advertisers, campaigns=campaigns,
        ui=_ui(lang), adv_ui=adv_ui, lang=lang, active="advertising",
    )


@advertising_bp.route("/admin/publicidad/anuncios/<int:banner_id>/editar", methods=["GET", "POST"])
@login_required
@admin_required
def banner_edit(banner_id):
    _only_admin()
    lang = _lang()
    adv_ui = _adv_ui(lang)
    banner      = BannerAd.query.get_or_404(banner_id)
    zones       = AdZone.query.order_by(AdZone.display_name).all()
    advertisers = Advertiser.query.filter_by(is_active=True).order_by(Advertiser.company_name).all()
    campaigns   = AdCampaign.query.order_by(AdCampaign.advertiser_id, AdCampaign.name).all()
    if request.method == "POST":
        _save_banner(banner, adv_ui)
        flash(adv_ui["saved"], "success")
        return redirect(url_for("advertising.banners_list"))
    return render_template(
        "admin/adv_banner_form.html",
        banner=banner, zones=zones, advertisers=advertisers, campaigns=campaigns,
        ui=_ui(lang), adv_ui=adv_ui, lang=lang, active="advertising",
    )


@advertising_bp.route("/admin/publicidad/anuncios/<int:banner_id>/eliminar", methods=["POST"])
@login_required
@admin_required
def banner_delete(banner_id):
    _only_admin()
    lang = _lang()
    banner = BannerAd.query.get_or_404(banner_id)
    db.session.delete(banner)
    db.session.commit()
    flash(_adv_ui(lang)["deleted"], "success")
    return redirect(url_for("advertising.banners_list"))


@advertising_bp.route("/admin/publicidad/anuncios/<int:banner_id>/toggle", methods=["POST"])
@login_required
@admin_required
def banner_toggle(banner_id):
    _only_admin()
    lang = _lang()
    adv_ui = _adv_ui(lang)
    banner = BannerAd.query.get_or_404(banner_id)
    banner.is_active = not banner.is_active
    db.session.commit()
    flash(adv_ui["toggled_on"] if banner.is_active else adv_ui["toggled_off"], "success")
    return redirect(url_for("advertising.banners_list"))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_date(val):
    if not val:
        return None
    try:
        return date.fromisoformat(val)
    except ValueError:
        return None


def _save_banner(banner, ui):
    """Create or update a BannerAd from POST data. Commits to DB."""
    f = request.form
    ad_type       = f.get("ad_type", "image")
    content       = f.get("content", "").strip()
    click_url     = f.get("click_url", "").strip() or None
    zone_id       = int(f.get("zone_id") or 0)
    advertiser_id = f.get("advertiser_id") or None
    campaign_id   = f.get("campaign_id") or None
    if advertiser_id:
        advertiser_id = int(advertiser_id)
    if campaign_id:
        campaign_id = int(campaign_id)
        # sync advertiser from campaign if not explicitly set
        if not advertiser_id:
            c = AdCampaign.query.get(campaign_id)
            if c:
                advertiser_id = c.advertiser_id
    is_active  = bool(f.get("is_active"))
    start_date = _parse_date(f.get("start_date"))
    end_date   = _parse_date(f.get("end_date"))

    if banner is None:
        banner = BannerAd()
        db.session.add(banner)

    def _clean_countries(raw):
        codes = [c.strip().upper() for c in (raw or "").split(",") if c.strip()]
        return ",".join(codes) or None

    banner.name              = f.get("name", "").strip() or None
    banner.ad_type           = ad_type
    banner.content           = content
    banner.click_url         = click_url
    banner.zone_id           = zone_id
    banner.advertiser_id     = advertiser_id
    banner.campaign_id       = campaign_id
    banner.is_active         = is_active
    banner.start_date        = start_date
    banner.end_date          = end_date
    banner.target_countries  = _clean_countries(f.get("target_countries"))
    banner.blocked_countries = _clean_countries(f.get("blocked_countries"))
    db.session.commit()

# ---------------------------------------------------------------------------
# Admin: Campaigns
# ---------------------------------------------------------------------------

@advertising_bp.route("/admin/publicidad/campanas/")
@login_required
@admin_required
def campaigns_list():
    _only_admin()
    lang = _lang()
    campaigns   = AdCampaign.query.order_by(AdCampaign.advertiser_id, AdCampaign.name).all()
    advertisers = Advertiser.query.order_by(Advertiser.company_name).all()
    return render_template(
        "admin/adv_campaigns.html",
        campaigns=campaigns, advertisers=advertisers,
        ui=_ui(lang), adv_ui=_adv_ui(lang), lang=lang, active="advertising",
    )


@advertising_bp.route("/admin/publicidad/campanas/nueva", methods=["GET", "POST"])
@login_required
@admin_required
def campaign_create():
    _only_admin()
    lang = _lang()
    adv_ui      = _adv_ui(lang)
    advertisers = Advertiser.query.filter_by(is_active=True).order_by(Advertiser.company_name).all()
    if request.method == "POST":
        adv_id = request.form.get("advertiser_id") or None
        c = AdCampaign(
            name          = request.form.get("name", "").strip(),
            category      = request.form.get("category") or None,
            advertiser_id = int(adv_id) if adv_id else None,
            is_active     = bool(request.form.get("is_active")),
        )
        db.session.add(c)
        db.session.commit()
        flash(adv_ui["saved"], "success")
        return redirect(url_for("advertising.campaigns_list"))
    cat_labels = CATEGORY_LABELS[lang]
    return render_template(
        "admin/adv_campaign_form.html",
        campaign=None, advertisers=advertisers, cat_labels=cat_labels,
        ui=_ui(lang), adv_ui=adv_ui, lang=lang, active="advertising",
    )


@advertising_bp.route("/admin/publicidad/campanas/<int:cid>/editar", methods=["GET", "POST"])
@login_required
@admin_required
def campaign_edit(cid):
    _only_admin()
    lang = _lang()
    adv_ui      = _adv_ui(lang)
    campaign    = AdCampaign.query.get_or_404(cid)
    advertisers = Advertiser.query.filter_by(is_active=True).order_by(Advertiser.company_name).all()
    if request.method == "POST":
        adv_id = request.form.get("advertiser_id") or None
        campaign.name          = request.form.get("name", "").strip()
        campaign.category      = request.form.get("category") or None
        campaign.advertiser_id = int(adv_id) if adv_id else None
        campaign.is_active     = bool(request.form.get("is_active"))
        db.session.commit()
        flash(adv_ui["saved"], "success")
        return redirect(url_for("advertising.campaigns_list"))
    cat_labels = CATEGORY_LABELS[lang]
    return render_template(
        "admin/adv_campaign_form.html",
        campaign=campaign, advertisers=advertisers, cat_labels=cat_labels,
        ui=_ui(lang), adv_ui=adv_ui, lang=lang, active="advertising",
    )


@advertising_bp.route("/admin/publicidad/campanas/<int:cid>/eliminar", methods=["POST"])
@login_required
@admin_required
def campaign_delete(cid):
    _only_admin()
    lang = _lang()
    campaign = AdCampaign.query.get_or_404(cid)
    db.session.delete(campaign)
    db.session.commit()
    flash(_adv_ui(lang)["deleted"], "success")
    return redirect(url_for("advertising.campaigns_list"))


@advertising_bp.route("/admin/publicidad/campanas/por-cliente")
@login_required
@admin_required
def campaigns_by_advertiser():
    """JSON endpoint: returns campaigns filtered by advertiser_id."""
    _only_admin()
    adv_id = request.args.get("advertiser_id")
    q = AdCampaign.query.filter_by(is_active=True)
    if adv_id and adv_id.isdigit():
        q = q.filter_by(advertiser_id=int(adv_id))
    from flask import jsonify
    return jsonify([{"id": c.id, "name": c.name} for c in q.order_by(AdCampaign.name).all()])

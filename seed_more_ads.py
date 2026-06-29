"""
seed_more_ads.py — Additional demo advertisers, campaigns and banner ads.
Run after migrate18.py: python seed_more_ads.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models import Advertiser, AdCampaign, AdZone, BannerAd

app = create_app()

# ── New advertisers ──────────────────────────────────────────────────────────
NEW_ADVERTISERS = [
    {"company_name": "Inca Kola",         "contact_name": "Rosa Mendoza",   "contact_email": "rosa@incakola.pe"},
    {"company_name": "Pilsen Callao",     "contact_name": "Jorge Paredes",  "contact_email": "jorge@pilsen.pe"},
    {"company_name": "Interbank",         "contact_name": "Carla Ríos",     "contact_email": "carla@interbank.pe"},
    {"company_name": "Entel Perú",        "contact_name": "Miguel Salas",   "contact_email": "miguel@entel.pe"},
    {"company_name": "Saga Falabella",    "contact_name": "Patricia Vega",  "contact_email": "patricia@falabella.com.pe"},
]

# ── Campaigns (new + update categories for existing ones) ────────────────────
# Existing campaign ids: 1=Verano2025(coke), 2=Cuenta BCP Digital, 3=Cristal
EXISTING_CAMP_CATEGORIES = {
    1: "seasonal",       # Verano 2025 → Estacional
    2: "conversion",     # Cuenta BCP Digital → Conversión
    3: "awareness",      # Cristal – Hecho con amor → Branding
}

# New campaigns keyed by advertiser company_name
NEW_CAMPAIGNS = [
    # Coca-Cola Perú (existing)
    {"advertiser": "Coca-Cola Perú",  "name": "Happiness Always",          "category": "awareness"},
    # BCP (existing)
    {"advertiser": "BCP",             "name": "BCP Cashback Navidad",       "category": "seasonal"},
    # Backus (existing)
    {"advertiser": "Backus",          "name": "Backus Institucional 2025",  "category": "institutional"},
    # New advertisers
    {"advertiser": "Inca Kola",       "name": "La bebida del Perú",         "category": "awareness"},
    {"advertiser": "Inca Kola",       "name": "Inca Kola Navidad 2025",     "category": "seasonal"},
    {"advertiser": "Pilsen Callao",   "name": "Pilsen – El sabor de Lima",  "category": "awareness"},
    {"advertiser": "Pilsen Callao",   "name": "Pilsen Retargeting Web",     "category": "retargeting"},
    {"advertiser": "Interbank",       "name": "Tarjeta Visa Interbank",     "category": "conversion"},
    {"advertiser": "Interbank",       "name": "App Interbank – Lanzamiento","category": "launch"},
    {"advertiser": "Entel Perú",      "name": "Plan 5G Entel",              "category": "launch"},
    {"advertiser": "Entel Perú",      "name": "Entel Retargeting",          "category": "retargeting"},
    {"advertiser": "Saga Falabella",  "name": "Cyberdays 2025",             "category": "seasonal"},
    {"advertiser": "Saga Falabella",  "name": "Colección Invierno",         "category": "conversion"},
]

# ── Banners ──────────────────────────────────────────────────────────────────
# Format: name, campaign, zone_key, ad_type, content, click_url,
#         target_countries (opt), blocked_countries (opt), is_active (opt)
NEW_BANNERS = [
    # ── Coca-Cola Perú ──────────────────────────────────────────────────────
    {"name": "Happiness header",    "campaign": "Happiness Always",
     "zone": "header_banner",      "type": "image",
     "content": "https://images.unsplash.com/photo-1543637005-4d639a4e16de?w=970&h=90&fit=crop",
     "url": "https://www.cocacola.com.pe/", "target": "PE,CL,CO"},

    # ── Inca Kola ───────────────────────────────────────────────────────────
    {"name": "Inca Kola sidebar",   "campaign": "La bebida del Perú",
     "zone": "sidebar_news",       "type": "image",
     "content": "https://images.unsplash.com/photo-1629203851122-3726ecdf080e?w=300&h=250&fit=crop",
     "url": "https://www.incakola.com.pe/", "target": "PE"},

    {"name": "Inca Kola leaderboard","campaign": "La bebida del Perú",
     "zone": "catalog_inline",     "type": "image",
     "content": "https://images.unsplash.com/photo-1621939514649-280e2ee25f60?w=728&h=90&fit=crop",
     "url": "https://www.incakola.com.pe/", "target": "PE"},

    {"name": "Navidad Inca Kola",   "campaign": "Inca Kola Navidad 2025",
     "zone": "header_banner",      "type": "image",
     "content": "https://images.unsplash.com/photo-1512909006721-3d6018887383?w=970&h=90&fit=crop",
     "url": "https://www.incakola.com.pe/", "target": "PE", "active": False},

    # ── Pilsen Callao ───────────────────────────────────────────────────────
    {"name": "Pilsen sidebar",      "campaign": "Pilsen – El sabor de Lima",
     "zone": "sidebar_news",       "type": "image",
     "content": "https://images.unsplash.com/photo-1574391884720-bbc3740c59d1?w=300&h=250&fit=crop",
     "url": "https://www.pilsencallao.com.pe/", "target": "PE"},

    {"name": "Pilsen header",       "campaign": "Pilsen – El sabor de Lima",
     "zone": "header_banner",      "type": "image",
     "content": "https://images.unsplash.com/photo-1559526323-cb2f2fe2591b?w=970&h=90&fit=crop",
     "url": "https://www.pilsencallao.com.pe/", "target": "PE,CL"},

    {"name": "Pilsen retargeting rect","campaign": "Pilsen Retargeting Web",
     "zone": "sidebar_news",       "type": "image",
     "content": "https://images.unsplash.com/photo-1566633806327-68e152aaf26d?w=300&h=250&fit=crop",
     "url": "https://www.pilsencallao.com.pe/", "target": "PE"},

    # ── Interbank ───────────────────────────────────────────────────────────
    {"name": "Visa Interbank banner","campaign": "Tarjeta Visa Interbank",
     "zone": "header_banner",      "type": "image",
     "content": "https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?w=970&h=90&fit=crop",
     "url": "https://www.interbank.pe/", "target": "PE"},

    {"name": "Visa Interbank sidebar","campaign": "Tarjeta Visa Interbank",
     "zone": "sidebar_news",       "type": "image",
     "content": "https://images.unsplash.com/photo-1562577309-4932fdd64cd1?w=300&h=250&fit=crop",
     "url": "https://www.interbank.pe/", "target": "PE"},

    {"name": "App Interbank video", "campaign": "App Interbank – Lanzamiento",
     "zone": "sidebar_news",       "type": "video",
     "content": "https://www.w3schools.com/html/mov_bbb.mp4",
     "url": "https://www.interbank.pe/app", "target": "PE"},

    {"name": "App Interbank inline","campaign": "App Interbank – Lanzamiento",
     "zone": "catalog_inline",     "type": "image",
     "content": "https://images.unsplash.com/photo-1563986768494-4dee2763ff3f?w=728&h=90&fit=crop",
     "url": "https://www.interbank.pe/app", "target": "PE"},

    # ── Entel ───────────────────────────────────────────────────────────────
    {"name": "5G Entel header",     "campaign": "Plan 5G Entel",
     "zone": "header_banner",      "type": "image",
     "content": "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=970&h=90&fit=crop",
     "url": "https://www.entel.pe/", "target": "PE,CL"},

    {"name": "5G Entel sidebar",    "campaign": "Plan 5G Entel",
     "zone": "sidebar_news",       "type": "image",
     "content": "https://images.unsplash.com/photo-1526406915894-7bcd65f60845?w=300&h=250&fit=crop",
     "url": "https://www.entel.pe/", "target": "PE"},

    {"name": "Entel retargeting banner","campaign": "Entel Retargeting",
     "zone": "catalog_inline",     "type": "image",
     "content": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=728&h=90&fit=crop",
     "url": "https://www.entel.pe/", "target": "PE,CL", "active": False},

    # ── Saga Falabella ──────────────────────────────────────────────────────
    {"name": "Cyberdays header",    "campaign": "Cyberdays 2025",
     "zone": "header_banner",      "type": "image",
     "content": "https://images.unsplash.com/photo-1607082348824-0a96f2a4b9da?w=970&h=90&fit=crop",
     "url": "https://www.falabella.com.pe/", "target": "PE,CL,CO,AR"},

    {"name": "Cyberdays sidebar",   "campaign": "Cyberdays 2025",
     "zone": "sidebar_news",       "type": "image",
     "content": "https://images.unsplash.com/photo-1571781926291-c477ebfd024b?w=300&h=250&fit=crop",
     "url": "https://www.falabella.com.pe/", "target": "PE,CL,CO,AR"},

    {"name": "Colección Invierno inline","campaign": "Colección Invierno",
     "zone": "catalog_inline",     "type": "image",
     "content": "https://images.unsplash.com/photo-1490481651871-ab68de25d43d?w=728&h=90&fit=crop",
     "url": "https://www.falabella.com.pe/", "blocked": "MX,BR"},

    {"name": "Colección Invierno sidebar","campaign": "Colección Invierno",
     "zone": "sidebar_news_lower", "type": "image",
     "content": "https://images.unsplash.com/photo-1445205170230-053b83016050?w=300&h=250&fit=crop",
     "url": "https://www.falabella.com.pe/", "blocked": "MX,BR"},

    # ── BCP extra ───────────────────────────────────────────────────────────
    {"name": "BCP Navidad sidebar", "campaign": "BCP Cashback Navidad",
     "zone": "sidebar_news",       "type": "image",
     "content": "https://images.unsplash.com/photo-1576081899960-fd9ae2e72af1?w=300&h=250&fit=crop",
     "url": "https://www.viabcp.com/", "target": "PE"},

    {"name": "BCP Navidad header",  "campaign": "BCP Cashback Navidad",
     "zone": "header_banner",      "type": "image",
     "content": "https://images.unsplash.com/photo-1513885535751-8b9238bd345a?w=970&h=90&fit=crop",
     "url": "https://www.viabcp.com/", "target": "PE"},

    # ── Backus extra ────────────────────────────────────────────────────────
    {"name": "Backus Institucional header","campaign": "Backus Institucional 2025",
     "zone": "header_banner",      "type": "image",
     "content": "https://images.unsplash.com/photo-1518791841217-8f162f1912da?w=970&h=90&fit=crop",
     "url": "https://www.backus.pe/", "target": "PE"},
]

with app.app_context():
    # -- Update existing campaign categories --------------------------------
    for camp_id, cat in EXISTING_CAMP_CATEGORIES.items():
        c = AdCampaign.query.get(camp_id)
        if c and not c.category:
            c.category = cat
            print(f"  ~ Campaign #{camp_id}: category → {cat}")
    db.session.flush()

    # -- Create new advertisers ---------------------------------------------
    adv_map = {a.company_name: a.id for a in Advertiser.query.all()}
    for a in NEW_ADVERTISERS:
        if a["company_name"] not in adv_map:
            adv = Advertiser(
                company_name=a["company_name"],
                contact_name=a["contact_name"],
                contact_email=a["contact_email"],
                is_active=True,
            )
            db.session.add(adv)
            db.session.flush()
            adv_map[a["company_name"]] = adv.id
            print(f"  + Advertiser: {a['company_name']}")

    # -- Create new campaigns -----------------------------------------------
    camp_map = {c.name: c.id for c in AdCampaign.query.all()}
    for c in NEW_CAMPAIGNS:
        if c["name"] not in camp_map:
            camp = AdCampaign(
                name=c["name"],
                category=c.get("category"),
                advertiser_id=adv_map.get(c["advertiser"]),
                is_active=True,
            )
            db.session.add(camp)
            db.session.flush()
            camp_map[c["name"]] = camp.id
            print(f"  + Campaign: {c['name']} ({c['advertiser']}) [{c.get('category','')}]")

    # -- Create new banners -------------------------------------------------
    zone_map = {z.zone_key: z.id for z in AdZone.query.all()}
    for b in NEW_BANNERS:
        zone_id = zone_map.get(b["zone"])
        if not zone_id:
            print(f"  ! Zone not found: {b['zone']} — skipping {b['name']}")
            continue
        camp_id = camp_map.get(b["campaign"])
        if not camp_id:
            print(f"  ! Campaign not found: {b['campaign']} — skipping {b['name']}")
            continue
        camp_obj = AdCampaign.query.get(camp_id)
        banner = BannerAd(
            name=b["name"],
            zone_id=zone_id,
            advertiser_id=camp_obj.advertiser_id if camp_obj else None,
            campaign_id=camp_id,
            ad_type=b["type"],
            content=b["content"],
            click_url=b.get("url"),
            target_countries=b.get("target"),
            blocked_countries=b.get("blocked"),
            is_active=b.get("active", True),
            impressions_count=__import__('random').randint(0, 45000),
            clicks_count=__import__('random').randint(0, 1200),
        )
        db.session.add(banner)
        print(f"  + Banner: {b['name']}  [{b['zone']}]  geo={b.get('target') or ('blocked:'+b.get('blocked','')) or 'global'}")

    db.session.commit()
    print("\n── Totals ──────────────────────")
    print(f"  Advertisers: {Advertiser.query.count()}")
    print(f"  Campaigns:   {AdCampaign.query.count()}")
    print(f"  Banner ads:  {BannerAd.query.count()}")

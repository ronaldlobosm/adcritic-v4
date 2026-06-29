"""
Seed demo advertisers, campaigns, and banner ads across all 3 zones.
Run once: python seed_ads.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models import Advertiser, AdCampaign, AdZone, BannerAd

app = create_app()

ADVERTISERS = [
    {"company_name": "Coca-Cola Perú",    "contact_name": "Ana Torres",    "contact_email": "ana@coke.pe"},
    {"company_name": "BCP",               "contact_name": "Luis Ríos",     "contact_email": "luis@bcp.com.pe"},
    {"company_name": "Backus",            "contact_name": "Marta Fuentes",  "contact_email": "marta@backus.pe"},
]

CAMPAIGNS = [
    {"advertiser": "Coca-Cola Perú", "name": "Verano 2025"},
    {"advertiser": "BCP",            "name": "Cuenta BCP Digital"},
    {"advertiser": "Backus",         "name": "Cristal – Hecho con amor"},
]

# Real-world free-to-use image & video URLs for demo
BANNERS = [
    # ── header_banner (970×90) ──────────────────────────────────────────────
    {
        "name":        "Header Coca-Cola verano",
        "zone_key":    "header_banner",
        "advertiser":  "Coca-Cola Perú",
        "campaign":    "Verano 2025",
        "ad_type":     "image",
        "content":     "https://images.unsplash.com/photo-1554866585-cd94860890b7?w=970&h=90&fit=crop",
        "click_url":   "https://www.cocacola.com.pe/",
    },
    {
        "name":        "Header BCP digital",
        "zone_key":    "header_banner",
        "advertiser":  "BCP",
        "campaign":    "Cuenta BCP Digital",
        "ad_type":     "image",
        "content":     "https://images.unsplash.com/photo-1563013544-824ae1b704d3?w=970&h=90&fit=crop",
        "click_url":   "https://www.viabcp.com/",
    },
    {
        "name":        "Header Cristal",
        "zone_key":    "header_banner",
        "advertiser":  "Backus",
        "campaign":    "Cristal – Hecho con amor",
        "ad_type":     "image",
        "content":     "https://images.unsplash.com/photo-1608270586620-248524c67de9?w=970&h=90&fit=crop",
        "click_url":   "https://www.backus.pe/",
    },

    # ── catalog_inline (728×90) ─────────────────────────────────────────────
    {
        "name":        "Leaderboard BCP",
        "zone_key":    "catalog_inline",
        "advertiser":  "BCP",
        "campaign":    "Cuenta BCP Digital",
        "ad_type":     "image",
        "content":     "https://images.unsplash.com/photo-1559526324-4b87b5e36e44?w=728&h=90&fit=crop",
        "click_url":   "https://www.viabcp.com/",
    },
    {
        "name":        "Leaderboard Coca-Cola",
        "zone_key":    "catalog_inline",
        "advertiser":  "Coca-Cola Perú",
        "campaign":    "Verano 2025",
        "ad_type":     "image",
        "content":     "https://images.unsplash.com/photo-1581005830583-6f3a7b3c8d0a?w=728&h=90&fit=crop",
        "click_url":   "https://www.cocacola.com.pe/",
    },

    # ── sidebar_news (300×250) ──────────────────────────────────────────────
    {
        "name":        "Medium rect Backus",
        "zone_key":    "sidebar_news",
        "advertiser":  "Backus",
        "campaign":    "Cristal – Hecho con amor",
        "ad_type":     "image",
        "content":     "https://images.unsplash.com/photo-1510812431401-41d2bd2722f3?w=300&h=250&fit=crop",
        "click_url":   "https://www.backus.pe/",
    },
    {
        "name":        "Medium rect Coca-Cola",
        "zone_key":    "sidebar_news",
        "advertiser":  "Coca-Cola Perú",
        "campaign":    "Verano 2025",
        "ad_type":     "image",
        "content":     "https://images.unsplash.com/photo-1534353436294-0dbd4bdac845?w=300&h=250&fit=crop",
        "click_url":   "https://www.cocacola.com.pe/",
    },
    {
        "name":        "Video BCP sidebar",
        "zone_key":    "sidebar_news",
        "advertiser":  "BCP",
        "campaign":    "Cuenta BCP Digital",
        "ad_type":     "video",
        "content":     "https://www.w3schools.com/html/mov_bbb.mp4",
        "click_url":   "https://www.viabcp.com/",
    },
]

with app.app_context():
    # Create advertisers
    adv_map = {}
    for a in ADVERTISERS:
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

    # Create campaigns
    camp_map = {}
    for c in CAMPAIGNS:
        camp = AdCampaign(
            name=c["name"],
            advertiser_id=adv_map[c["advertiser"]],
            is_active=True,
        )
        db.session.add(camp)
        db.session.flush()
        camp_map[c["name"]] = camp.id
        print(f"  + Campaign: {c['name']} ({c['advertiser']})")

    # Create banners
    zone_map = {z.zone_key: z.id for z in AdZone.query.all()}
    for b in BANNERS:
        banner = BannerAd(
            name=b["name"],
            zone_id=zone_map[b["zone_key"]],
            advertiser_id=adv_map.get(b["advertiser"]),
            campaign_id=camp_map.get(b.get("campaign")),
            ad_type=b["ad_type"],
            content=b["content"],
            click_url=b.get("click_url"),
            is_active=True,
        )
        db.session.add(banner)
        print(f"  + Banner [{b['zone_key']}] "{b['name']}"")

    db.session.commit()
    print("\nDone. Totals:")
    print(f"  Advertisers: {Advertiser.query.count()}")
    print(f"  Campaigns:   {AdCampaign.query.count()}")
    print(f"  Banner ads:  {BannerAd.query.count()}")

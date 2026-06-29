"""
Add campaigns + names to existing demo banner ads.
Run once after migrate17.py: python seed_campaigns.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models import Advertiser, AdCampaign, BannerAd

app = create_app()

CAMPAIGNS = [
    {"advertiser": "Coca-Cola Perú", "name": "Verano 2025"},
    {"advertiser": "BCP",            "name": "Cuenta BCP Digital"},
    {"advertiser": "Backus",         "name": "Cristal – Hecho con amor"},
]

# Maps banner id → name + campaign name
BANNER_UPDATES = {
    1: {"name": "Header Coca-Cola verano",    "campaign": "Verano 2025"},
    2: {"name": "Header BCP digital",         "campaign": "Cuenta BCP Digital"},
    3: {"name": "Header Cristal",             "campaign": "Cristal – Hecho con amor"},
    4: {"name": "Leaderboard BCP",            "campaign": "Cuenta BCP Digital"},
    5: {"name": "Leaderboard Coca-Cola",      "campaign": "Verano 2025"},
    6: {"name": "Medium rect Backus",         "campaign": "Cristal – Hecho con amor"},
    7: {"name": "Medium rect Coca-Cola",      "campaign": "Verano 2025"},
    8: {"name": "Video BCP sidebar",          "campaign": "Cuenta BCP Digital"},
}

with app.app_context():
    adv_map = {a.company_name: a.id for a in Advertiser.query.all()}

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
        print(f"  + Campaign: {c['name']}")

    # Update banners
    for bid, upd in BANNER_UPDATES.items():
        b = BannerAd.query.get(bid)
        if b:
            b.name        = upd["name"]
            b.campaign_id = camp_map.get(upd["campaign"])
            print(f"  ~ Banner #{bid}: '{b.name}'  campaign={b.campaign_id}")

    db.session.commit()
    print("\nDone.")

import random
from datetime import datetime, timedelta, timezone



CHANNELS = ["facebook_ads", "google_ads", "instagram_ads", "email_campaign"]


def generate_campaigns(count: int = 8) -> list[dict]:
    random.seed(42)
    campaigns = []
    for i in range(count):
        campaigns.append({
            "external_id": f"CAMP-{2000 + i}",
            "name": f"{random.choice(['Summer', 'Winter', 'Spring', 'Flash'])} Sale {2026}",
            "channel": random.choice(CHANNELS),
        })
    return campaigns


def generate_marketing_spend(campaigns: list[dict], days: int = 180) -> list[dict]:
    random.seed(42)
    """
    Generates daily marketing spend per campaign, with one intentional
    anomaly: a spend spike with no matching revenue lift (Section 19 example).
    """
    spend_records = []
    start_date = (datetime.now(timezone.utc) - timedelta(days=days)).replace(hour=0, minute=0, second=0, microsecond=0)
    anomaly_day_spend_spike = days - 20  # planted on purpose

    for campaign in campaigns:
        base_daily_spend = random.uniform(50, 400)
        for day_offset in range(days):
            current_date = start_date + timedelta(days=day_offset)
            amount = base_daily_spend * random.uniform(0.8, 1.2)

            if day_offset == anomaly_day_spend_spike:
                amount *= 4  # unusual spend spike, planted

            spend_records.append({
                "campaign_external_id": campaign["external_id"],
                "spend_date": current_date.date().isoformat(),
                "amount": round(amount, 2),
            })
    return spend_records
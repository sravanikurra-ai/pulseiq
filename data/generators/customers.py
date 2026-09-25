import random
from datetime import datetime, timedelta, timezone
from faker import Faker

fake = Faker()

REGIONS = ["North America", "Europe", "Asia Pacific", "Latin America"]
CHANNELS = ["organic", "paid_social", "paid_search", "referral", "email"]


def generate_customers(count: int = 500, days: int = 180) -> list[dict]:
    Faker.seed(42)
    random.seed(42)
    fake.unique.clear()

    start_date = (datetime.now(timezone.utc) - timedelta(days=days)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    customers = []
    for i in range(count):
        # Spread customer acquisition realistically across the same window as orders,
        # instead of all being "created" at ingestion time.
        created_at = start_date + timedelta(
            days=random.randint(0, days - 1), hours=random.randint(0, 23)
        )
        customers.append({
            "external_id": f"CUST-{10000 + i}",
            "full_name": fake.name(),
            "email": fake.unique.email(),
            "region": random.choice(REGIONS),
            "acquisition_channel": random.choices(CHANNELS, weights=[35, 25, 20, 12, 8])[0],
            "created_at": created_at,
        })
    return customers
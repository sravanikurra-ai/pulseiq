import random
from faker import Faker

fake = Faker()
Faker.seed(42)
random.seed(42)

REGIONS = ["North America", "Europe", "Asia Pacific", "Latin America"]
CHANNELS = ["organic", "paid_social", "paid_search", "referral", "email"]


def generate_customers(count: int = 500) -> list[dict]:
    """
    Generates a list of fake customer records, shaped like what a real
    CRM API would return in its JSON response.
    """
    customers = []
    for i in range(count):
        customers.append({
            "external_id": f"CUST-{10000 + i}",
            "full_name": fake.name(),
            "email": fake.unique.email(),
            "region": random.choice(REGIONS),
            "acquisition_channel": random.choices(
                CHANNELS, weights=[35, 25, 20, 12, 8]
            )[0],
        })
    return customers
import random
from faker import Faker

fake = Faker()


CATEGORIES = ["Electronics", "Home & Kitchen", "Apparel", "Beauty", "Sports & Outdoors"]


def generate_products(count: int = 40) -> list[dict]:
    random.seed(42)
    """
    Generates a fake product catalog, shaped like a real product API response.
    """
    products = []
    for i in range(count):
        category = random.choice(CATEGORIES)
        # Rough realistic price ranges per category
        price_ranges = {
            "Electronics": (25, 800),
            "Home & Kitchen": (10, 250),
            "Apparel": (15, 120),
            "Beauty": (8, 90),
            "Sports & Outdoors": (12, 300),
        }
        low, high = price_ranges[category]
        products.append({
            "external_id": f"PROD-{1000 + i}",
            "name": fake.catch_phrase(),
            "category": category,
            "unit_price": round(random.uniform(low, high), 2),
        })
    return products
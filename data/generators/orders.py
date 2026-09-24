import random
from datetime import datetime, timedelta, timezone

random.seed(42)

STATUSES = ["completed", "completed", "completed", "completed", "cancelled", "refunded"]
CHANNELS = ["web", "mobile_app"]
REGIONS = ["North America", "Europe", "Asia Pacific", "Latin America"]


def generate_orders(
    customers: list[dict],
    products: list[dict],
    days: int = 180,
    base_orders_per_day: int = 25,
) -> list[dict]:
    """
    Generates fake order records across a date range, with:
    - normal day-to-day random variation
    - a gentle upward growth trend (so forecasting has something real to model)
    - a few INTENTIONAL anomalies planted (so anomaly detection has something to find)

    Shaped like what a real Orders API would return.
    """
    orders = []
    order_counter = 1
    start_date = (datetime.now(timezone.utc) - timedelta(days=days)).replace(
    hour=0, minute=0, second=0, microsecond=0
)

    # Plant 3 intentional anomaly days: a revenue crash, a spike, and an
    # unusual-region spike. We record these here so Phase 17 (evaluation)
    # can honestly check whether our model actually caught them.
    anomaly_day_crash = days // 3
    anomaly_day_spike = (days // 3) * 2
    anomaly_day_region_spike = days - 10

    for day_offset in range(days):
        current_date = start_date + timedelta(days=day_offset)

        # Gentle growth trend over time
        growth_factor = 1 + (day_offset / days) * 0.4
        orders_today = int(base_orders_per_day * growth_factor)

        # Normal daily randomness
        orders_today += random.randint(-5, 5)
        orders_today = max(orders_today, 1)

        # --- Intentional anomalies ---
        if day_offset == anomaly_day_crash:
            orders_today = max(int(orders_today * 0.15), 1)  # sudden crash
        elif day_offset == anomaly_day_spike:
            orders_today = int(orders_today * 3.5)           # sudden spike

        for _ in range(orders_today):
            customer = random.choice(customers)
            product = random.choice(products)
            quantity = random.randint(1, 4)
            unit_price = product["unit_price"]
            total_amount = round(unit_price * quantity, 2)

            region = customer["region"]
            if day_offset == anomaly_day_region_spike:
                region = "Latin America"  # unusual concentration, planted on purpose

            orders.append({
                "external_id": f"ORD-{100000 + order_counter}",
                "customer_external_id": customer["external_id"],
                "product_external_id": product["external_id"],
                "quantity": quantity,
                "total_amount": total_amount,
                "status": random.choice(STATUSES),
                "region": region,
                "channel": random.choice(CHANNELS),
                "order_date": (
                    current_date + timedelta(hours=random.randint(0, 23))
                ).isoformat(),
            })
            order_counter += 1

    return orders
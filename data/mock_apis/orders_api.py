from data.generators.orders import generate_orders


def fetch_orders(customers: list[dict], products: list[dict], days: int = 180, since_date=None) -> list[dict]:
    """
    Simulates calling a real Orders API's GET /orders endpoint.
    `since_date` is accepted for interface compatibility with incremental
    ingestion, matching how a real API would support a `?since=` query param
    — our mock always regenerates the full dataset internally, and the
    ingestion service filters by since_date after fetching.

    NOTE FOR FUTURE: replace this function's body with a real HTTP call to
    swap in a live Orders system, keeping the same return shape.
    """
    return generate_orders(customers, products, days=days)
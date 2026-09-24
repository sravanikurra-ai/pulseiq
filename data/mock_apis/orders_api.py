from data.generators.orders import generate_orders


def fetch_orders(customers: list[dict], products: list[dict], days: int = 180) -> list[dict]:
    """
    Simulates calling a real Orders API's GET /orders endpoint.

    NOTE FOR FUTURE: replace this function's body with a real HTTP call to
    swap in a live Orders system, keeping the same return shape.
    """
    return generate_orders(customers, products, days=days)
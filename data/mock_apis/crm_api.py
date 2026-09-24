from data.generators.customers import generate_customers


def fetch_customers(limit: int = 500) -> list[dict]:
    """
    Simulates calling a real CRM API's GET /customers endpoint.
    Returns a list of customer dicts, exactly as a real API's JSON body would.

    NOTE FOR FUTURE: to connect a real CRM, replace the body of this function
    with an actual HTTP call (e.g., using `httpx`), keeping the same
    function signature and return shape, so ingestion code never changes.
    """
    return generate_customers(count=limit)
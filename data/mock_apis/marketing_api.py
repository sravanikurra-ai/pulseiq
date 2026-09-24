from data.generators.marketing import generate_campaigns, generate_marketing_spend


def fetch_campaigns(count: int = 8) -> list[dict]:
    return generate_campaigns(count=count)


def fetch_marketing_spend(campaigns: list[dict], days: int = 180) -> list[dict]:
    return generate_marketing_spend(campaigns, days=days)
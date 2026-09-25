"""
Deliberately injects malformed records into otherwise-clean mock data,
so we can prove our validation logic actually rejects bad data — rather
than just assuming it works because our generators never produce bad data
naturally. Used only for testing, never in normal ingestion flow.
"""
import copy


def inject_bad_customers(customers: list[dict]) -> list[dict]:
    """Corrupts a few customer records in controlled, known ways."""
    corrupted = copy.deepcopy(customers)
    if len(corrupted) >= 5:
        corrupted[0]["full_name"] = ""            # blank required field
        corrupted[1]["email"] = "not-an-email"     # invalid email format
        corrupted[2]["external_id"] = ""           # blank external_id
    return corrupted


def inject_bad_orders(orders: list[dict]) -> list[dict]:
    """Corrupts a few order records in controlled, known ways."""
    corrupted = copy.deepcopy(orders)
    if len(corrupted) >= 5:
        corrupted[0]["quantity"] = -3                    # negative quantity
        corrupted[1]["total_amount"] = -50.00             # negative amount
        corrupted[2]["status"] = "pending_unknown_status"  # invalid status value
        corrupted[3]["order_date"] = "not-a-real-date"     # unparseable date
    return corrupted
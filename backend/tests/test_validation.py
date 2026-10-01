"""
Data validation tests, using the SAME controlled bad-data injector built
in Phase 8 — not new, separately-invented bad records. This proves the
production validation code and the test both agree on what "invalid" means.
"""
from pydantic import ValidationError
from app.schemas.ingestion_schemas import CustomerRecordSchema, OrderRecordSchema
from data.mock_apis.crm_api import fetch_customers
from data.generators.bad_data_injector import inject_bad_customers, inject_bad_orders
from data.generators.orders import generate_orders
from data.generators.products import generate_products


def test_bad_customer_records_are_rejected_with_correct_reasons():
    raw = fetch_customers(limit=10)
    corrupted = inject_bad_customers(raw)

    results = []
    for c in corrupted:
        try:
            CustomerRecordSchema(**c)
            results.append("valid")
        except ValidationError as e:
            results.append(e.errors()[0]["msg"])

    assert results.count("valid") == 7
    assert any("full_name" in r for r in results)
    assert any("email" in r for r in results)
    assert any("external_id" in r for r in results)


def test_valid_customer_records_are_never_falsely_rejected():
    """The inverse check: real, clean mock data must produce zero rejections."""
    raw = fetch_customers(limit=50)
    rejected = 0
    for c in raw:
        try:
            CustomerRecordSchema(**c)
        except ValidationError:
            rejected += 1
    assert rejected == 0


def test_bad_order_records_are_rejected():
    customers = fetch_customers(limit=5)
    products = generate_products(count=5)
    raw_orders = generate_orders(customers, products, days=5)
    corrupted = inject_bad_orders(raw_orders)

    invalid_count = 0
    for o in corrupted:
        try:
            OrderRecordSchema(**o)
        except ValidationError:
            invalid_count += 1
    assert invalid_count == 4  # negative quantity, negative amount, bad status, bad date
"""
Regression tests for the real idempotency bugs found during manual testing
in Phases 9, 11, and 13: ETL, anomaly detection, and alert generation must
each be safely re-runnable without duplicating rows.
"""
from datetime import date, timedelta
from app.models import Customer, Product, Order, FactOrdersDaily, Anomaly, Alert
from app.services.etl_service import run_etl
from app.services.anomaly_service import detect_anomalies
from app.services.alert_service import generate_alerts


def _seed_orders_for_etl(db, days=15):
    """Enough raw orders across enough days for ETL and anomaly detection to run meaningfully."""
    customer = Customer(external_id="CUST-1", full_name="Test Customer", region="North America")
    product = Product(external_id="PROD-1", name="Test Product", unit_price=50.00)
    db.add_all([customer, product])
    db.commit()

    for day_offset in range(days):
        order_date = date.today() - timedelta(days=day_offset)
        # One deliberate low-volume day to ensure anomaly detection has
        # something to flag across our small window.
        quantity_days = 1 if day_offset == 7 else 5
        for i in range(quantity_days):
            db.add(Order(
                external_id=f"ORD-{day_offset}-{i}", customer_id=customer.id, product_id=product.id,
                quantity=1, total_amount=50.00, status="completed",
                order_date=order_date,
            ))
    db.commit()


def test_etl_is_idempotent(db_session):
    """Regression test for Phase 9: running ETL twice must not duplicate fact rows."""
    _seed_orders_for_etl(db_session)

    run_etl(db_session)
    first_count = db_session.query(FactOrdersDaily).count()
    assert first_count > 0

    run_etl(db_session)
    second_count = db_session.query(FactOrdersDaily).count()

    assert second_count == first_count


def test_anomaly_detection_is_idempotent(db_session):
    """
    Regression test for the real Phase 11 bug: detect_anomalies previously
    appended new rows on every run instead of replacing prior results.
    """
    _seed_orders_for_etl(db_session, days=15)
    run_etl(db_session)

    detect_anomalies(db_session)
    first_count = db_session.query(Anomaly).count()

    detect_anomalies(db_session)
    second_count = db_session.query(Anomaly).count()

    assert second_count == first_count


def test_alert_generation_is_idempotent(db_session):
    """
    Regression test for Phase 13: generating alerts twice from the same
    anomalies must not create duplicate alerts, even if anomaly IDs change
    between runs (since detect_anomalies deletes and rebuilds them).
    """
    _seed_orders_for_etl(db_session, days=15)
    run_etl(db_session)
    detect_anomalies(db_session)

    generate_alerts(db_session)
    first_count = db_session.query(Alert).count()
    assert first_count > 0

    # Re-run anomaly detection (changes anomaly IDs) then generate alerts again —
    # this is the exact sequence that would have produced duplicates before the fix.
    detect_anomalies(db_session)
    generate_alerts(db_session)
    second_count = db_session.query(Alert).count()

    assert second_count == first_count
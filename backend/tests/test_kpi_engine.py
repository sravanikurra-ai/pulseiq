"""
KPI engine tests. These check the actual arithmetic, including the edge
cases the blueprint specifically calls out: zero orders, zero spend.
"""
from datetime import date, timedelta
from app.services import kpi_engine
from app.models import Customer, Product, Order


def _make_customer(db, external_id="CUST-1", region="North America"):
    c = Customer(external_id=external_id, full_name="Test Customer", region=region)
    db.add(c)
    db.commit()
    return c


def _make_product(db, external_id="PROD-1", price=100.00):
    p = Product(external_id=external_id, name="Test Product", unit_price=price)
    db.add(p)
    db.commit()
    return p


def _make_order(db, customer, product, quantity, total_amount, status="completed", days_ago=0):
    o = Order(
        external_id=f"ORD-{customer.id}-{product.id}-{days_ago}",
        customer_id=customer.id, product_id=product.id,
        quantity=quantity, total_amount=total_amount, status=status,
        order_date=date.today() - timedelta(days=days_ago),
    )
    db.add(o)
    db.commit()
    return o


def test_revenue_sums_only_completed_orders(db_session):
    """This requires fact_orders_daily, which our KPI engine reads from —
    see the ETL-dependent integration test below for the full-pipeline version.
    This test instead verifies the pure arithmetic by calling the underlying
    aggregation logic directly is out of scope; the real KPI functions read
    from FactOrdersDaily, so we test via that table directly."""
    from app.models import FactOrdersDaily
    db_session.add(FactOrdersDaily(
        order_date=date.today(), year=date.today().year, month=date.today().month,
        week=1, day_of_week="Monday", region="North America", channel="web",
        status="completed", order_count=2, total_revenue=300.00, total_quantity=2,
    ))
    db_session.add(FactOrdersDaily(
        order_date=date.today(), year=date.today().year, month=date.today().month,
        week=1, day_of_week="Monday", region="North America", channel="web",
        status="cancelled", order_count=1, total_revenue=999.00, total_quantity=1,
    ))
    db_session.commit()

    revenue = kpi_engine.calculate_revenue(db_session, date.today(), date.today())
    assert revenue == 300.00  # cancelled order's 999.00 must NOT be included


def test_aov_handles_zero_orders_without_crashing(db_session):
    """Edge case explicitly required by the blueprint: AOV must not divide by zero."""
    aov = kpi_engine.calculate_aov(db_session, date.today(), date.today())
    assert aov == 0.0


def test_growth_rate_handles_zero_previous_revenue(db_session):
    """Edge case: if the prior period had zero revenue, growth rate must not crash or return infinity."""
    rate = kpi_engine.calculate_growth_rate(db_session, date.today(), date.today())
    assert rate == 0.0


def test_cac_handles_zero_new_customers(db_session):
    """Edge case: if no customers were acquired, CAC must not divide by zero."""
    cac = kpi_engine.calculate_cac(db_session, date.today(), date.today())
    assert cac == 0.0


def test_marketing_roi_handles_zero_spend(db_session):
    """Edge case: if marketing spend was zero, ROI must not divide by zero."""
    roi = kpi_engine.calculate_marketing_roi(db_session, date.today(), date.today())
    assert roi == 0.0
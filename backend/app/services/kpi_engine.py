"""
Deterministic KPI engine. Every function here uses SQL aggregation and
plain Python arithmetic only — no ML, no LLM. This is Layer 1 of the
architecture (deterministic business logic), per Section 6 of the blueprint.
"""
import logging
from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func as sql_func

from app.models import FactOrdersDaily, Customer, MarketingSpend, Order, KPIResult

logger = logging.getLogger(__name__)


def calculate_revenue(db: Session, start: date, end: date) -> float:
    """Total revenue from completed orders in the period."""
    result = db.query(sql_func.sum(FactOrdersDaily.total_revenue)).filter(
        FactOrdersDaily.order_date >= start,
        FactOrdersDaily.order_date <= end,
        FactOrdersDaily.status == "completed",
    ).scalar()
    return float(result or 0)


def calculate_orders(db: Session, start: date, end: date) -> int:
    """Total count of completed orders in the period."""
    result = db.query(sql_func.sum(FactOrdersDaily.order_count)).filter(
        FactOrdersDaily.order_date >= start,
        FactOrdersDaily.order_date <= end,
        FactOrdersDaily.status == "completed",
    ).scalar()
    return int(result or 0)


def calculate_aov(db: Session, start: date, end: date) -> float:
    """Average Order Value = Revenue / Orders. Returns 0 if no orders (avoids divide-by-zero)."""
    revenue = calculate_revenue(db, start, end)
    orders = calculate_orders(db, start, end)
    if orders == 0:
        return 0.0
    return round(revenue / orders, 2)


def calculate_conversion_rate(db: Session, start: date, end: date) -> float:
    """
    PROXY conversion rate: completed orders / all orders (any status) in the period.
    LIMITATION: a real conversion rate requires website visit/session data,
    which this system does not ingest. This measures "of orders placed,
    what fraction completed successfully" — a meaningful but different metric
    from true funnel conversion (visitors -> buyers).
    """
    total = db.query(sql_func.sum(FactOrdersDaily.order_count)).filter(
        FactOrdersDaily.order_date >= start, FactOrdersDaily.order_date <= end,
    ).scalar()
    completed = calculate_orders(db, start, end)
    total = int(total or 0)
    if total == 0:
        return 0.0
    return round((completed / total) * 100, 2)


def calculate_cac(db: Session, start: date, end: date) -> float:
    """
    CAC = total marketing spend / new customers acquired in the period.
    LIMITATION: attributes ALL spend broadly to new customer acquisition,
    not per-channel — we don't have click-level attribution linking a
    specific customer to a specific campaign.
    """
    total_spend = db.query(sql_func.sum(MarketingSpend.amount)).filter(
        MarketingSpend.spend_date >= start, MarketingSpend.spend_date <= end,
    ).scalar()
    total_spend = float(total_spend or 0)

    new_customers = db.query(sql_func.count(Customer.id)).filter(
        sql_func.date(Customer.created_at) >= start,
        sql_func.date(Customer.created_at) <= end,
    ).scalar()
    new_customers = int(new_customers or 0)

    if new_customers == 0:
        return 0.0
    return round(total_spend / new_customers, 2)


def calculate_retention_rate(db: Session, period_start: date, period_end: date) -> float:
    """
    Retention rate = % of customers who ordered in the PREVIOUS period of
    equal length who also ordered in THIS period.
    """
    period_length = (period_end - period_start).days + 1
    prev_end = period_start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=period_length - 1)

    prev_customers = {
        row[0] for row in db.query(Order.customer_id).filter(
            sql_func.date(Order.order_date) >= prev_start,
            sql_func.date(Order.order_date) <= prev_end,
            Order.status == "completed",
        ).distinct().all()
    }

    if not prev_customers:
        return 0.0

    current_customers = {
        row[0] for row in db.query(Order.customer_id).filter(
            sql_func.date(Order.order_date) >= period_start,
            sql_func.date(Order.order_date) <= period_end,
            Order.status == "completed",
        ).distinct().all()
    }

    retained = prev_customers & current_customers
    return round((len(retained) / len(prev_customers)) * 100, 2)


def calculate_growth_rate(db: Session, period_start: date, period_end: date) -> float:
    """
    Revenue growth rate vs. the immediately preceding period of equal length.
    """
    period_length = (period_end - period_start).days + 1
    prev_end = period_start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=period_length - 1)

    current_revenue = calculate_revenue(db, period_start, period_end)
    previous_revenue = calculate_revenue(db, prev_start, prev_end)

    if previous_revenue == 0:
        return 0.0  # avoids divide-by-zero; a genuinely honest "undefined" case
    return round(((current_revenue - previous_revenue) / previous_revenue) * 100, 2)


def calculate_marketing_roi(db: Session, start: date, end: date) -> float:
    """
    Aggregate Marketing ROI = (Revenue - Marketing Spend) / Marketing Spend.
    LIMITATION: aggregate only, not per-campaign — our data model doesn't
    link individual orders to specific campaigns (would need UTM/click tracking).
    """
    revenue = calculate_revenue(db, start, end)
    spend = db.query(sql_func.sum(MarketingSpend.amount)).filter(
        MarketingSpend.spend_date >= start, MarketingSpend.spend_date <= end,
    ).scalar()
    spend = float(spend or 0)

    if spend == 0:
        return 0.0
    return round(((revenue - spend) / spend) * 100, 2)


KPI_CALCULATORS = {
    "revenue": calculate_revenue,
    "orders": calculate_orders,
    "aov": calculate_aov,
    "conversion_rate": calculate_conversion_rate,
    "cac": calculate_cac,
    "retention_rate": calculate_retention_rate,
    "growth_rate": calculate_growth_rate,
    "marketing_roi": calculate_marketing_roi,
}

KPI_LIMITATIONS = {
    "conversion_rate": "Proxy metric: completed orders / all orders. Not true visitor-to-buyer funnel conversion (no session data ingested).",
    "cac": "Attributes total marketing spend broadly to new customers acquired; not per-channel attributed.",
    "marketing_roi": "Aggregate ROI (total revenue vs total spend); not per-campaign attributed.",
}


def compute_and_store_kpi(db: Session, kpi_name: str, start: date, end: date) -> KPIResult:
    """
    Computes a single named KPI and persists it to kpi_results, so the
    dashboard/API can read pre-computed values instead of recalculating
    on every request.
    """
    if kpi_name not in KPI_CALCULATORS:
        raise ValueError(f"Unknown KPI: {kpi_name}")

    value = KPI_CALCULATORS[kpi_name](db, start, end)

    result = KPIResult(
        kpi_name=kpi_name,
        period_start=start,
        period_end=end,
        value=value,
    )
    db.add(result)
    db.commit()
    logger.info(f"KPI computed: {kpi_name} [{start} to {end}] = {value}")
    return result


def compute_all_kpis(db: Session, start: date, end: date) -> dict:
    """Computes and stores every KPI for the given period, returning a summary dict."""
    results = {}
    for kpi_name in KPI_CALCULATORS:
        value = KPI_CALCULATORS[kpi_name](db, start, end)
        db.add(KPIResult(kpi_name=kpi_name, period_start=start, period_end=end, value=value))
        results[kpi_name] = {
            "value": value,
            "note": KPI_LIMITATIONS.get(kpi_name),
        }
    db.commit()
    return results
"""
ETL service: transforms raw `orders` rows into the pre-aggregated
`fact_orders_daily` table. Extract = query raw orders. Transform = derive
date dimensions and aggregate. Load = delete-then-insert into the fact table.

Idempotent by design: re-running the ETL for a given date range always
deletes existing fact rows in that range first, then rebuilds them fresh —
so running it twice produces the same result, never duplicates.
"""
import logging
from datetime import date, datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func as sql_func

from app.models import Order, FactOrdersDaily

logger = logging.getLogger(__name__)


def run_etl(db: Session, start_date: date | None = None, end_date: date | None = None) -> dict:
    """
    Runs the ETL transform over the given date range (inclusive).
    If no range is given, processes the full history of orders present.
    """
    query = db.query(
        sql_func.date(Order.order_date).label("order_date"),
        Order.region,
        Order.channel,
        Order.status,
        sql_func.count(Order.id).label("order_count"),
        sql_func.sum(Order.total_amount).label("total_revenue"),
        sql_func.sum(Order.quantity).label("total_quantity"),
    ).group_by(
        sql_func.date(Order.order_date), Order.region, Order.channel, Order.status
    )

    if start_date:
        query = query.filter(sql_func.date(Order.order_date) >= start_date)
    if end_date:
        query = query.filter(sql_func.date(Order.order_date) <= end_date)

    aggregated_rows = query.all()

    if not aggregated_rows:
        logger.info("ETL: no orders found in the given range; nothing to transform.")
        return {"status": "success", "rows_processed": 0, "date_range": None}

    actual_dates = [row.order_date for row in aggregated_rows]
    range_start = min(actual_dates)
    range_end = max(actual_dates)

    # --- Load step: delete-then-insert for idempotency ---
    # Deleting only the affected date range (not the whole table) means
    # re-running the ETL for "yesterday" doesn't wipe out prior months.
    deleted_count = (
        db.query(FactOrdersDaily)
        .filter(FactOrdersDaily.order_date >= range_start, FactOrdersDaily.order_date <= range_end)
        .delete(synchronize_session=False)
    )

    new_fact_rows = []
    for row in aggregated_rows:
        order_date = row.order_date
        new_fact_rows.append(FactOrdersDaily(
            order_date=order_date,
            year=order_date.year,
            month=order_date.month,
            week=order_date.isocalendar()[1],
            day_of_week=order_date.strftime("%A"),
            region=row.region,
            channel=row.channel,
            status=row.status,
            order_count=row.order_count,
            total_revenue=row.total_revenue or 0,
            total_quantity=row.total_quantity or 0,
        ))

    db.add_all(new_fact_rows)
    db.commit()

    logger.info(
        f"ETL complete: range={range_start} to {range_end}, "
        f"deleted={deleted_count}, inserted={len(new_fact_rows)}"
    )

    return {
        "status": "success",
        "rows_processed": len(new_fact_rows),
        "rows_deleted_before_reload": deleted_count,
        "date_range": {"start": range_start.isoformat(), "end": range_end.isoformat()},
    }
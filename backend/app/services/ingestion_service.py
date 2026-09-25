"""
Ingestion service: pulls data from our mock APIs (standing in for real
Orders/CRM/Marketing systems), checks for duplicates, inserts new records,
and logs the outcome of every run. This is the real, re-runnable pipeline
entry point — unlike seed_database.py, this assumes the database may
already contain data and must not create duplicates.
"""
from pydantic import ValidationError
from app.schemas.ingestion_schemas import (
    CustomerRecordSchema, ProductRecordSchema, OrderRecordSchema, MarketingSpendRecordSchema,
)
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models import (
    Customer, Product, Order, MarketingCampaign, MarketingSpend,
    DataIngestionLog, DataQualityResult,
)

from data.mock_apis.crm_api import fetch_customers
from data.mock_apis.orders_api import fetch_orders
from data.mock_apis.marketing_api import fetch_campaigns, fetch_marketing_spend
from data.generators.products import generate_products

logger = logging.getLogger(__name__)


def _get_last_successful_ingestion_date(db: Session, source: str):
    """
    Supports incremental ingestion: finds the most recent successful run
    for a given source, so we only fetch orders newer than that.
    Returns None if no prior successful run exists (first-ever ingestion).
    """
    last_log = (
        db.query(DataIngestionLog)
        .filter(DataIngestionLog.source == source, DataIngestionLog.status == "success")
        .order_by(DataIngestionLog.finished_at.desc())
        .first()
    )
    return last_log.finished_at if last_log else None


def ingest_customers(db: Session) -> DataIngestionLog:
    """
    Ingests customer records from the (mock) CRM API.
    Skips records whose external_id already exists (idempotent).
    """
    log = DataIngestionLog(source="customers", status="failed", records_fetched=0, records_ingested=0)
    db.add(log)
    db.flush()  # assigns log.id without committing yet

    try:
        raw_customers = fetch_customers(limit=500)
        log.records_fetched = len(raw_customers)

        existing_ids = {
            row[0] for row in db.query(Customer.external_id).all()
        }
        valid_records = []
        invalid_count = 0
        for c in raw_customers:
            try:
                validated = CustomerRecordSchema(**c)
                valid_records.append(validated.model_dump())
            except ValidationError as ve:
                invalid_count += 1
                logger.warning(f"Rejected invalid customer record {c.get('external_id')}: {ve.errors()}")

        new_customers = [
            Customer(**c) for c in valid_records if c["external_id"] not in existing_ids
        ]
        db.add_all(new_customers)
        log.records_ingested = len(new_customers)

        duplicate_count = len(valid_records) - len(new_customers)

        quality = DataQualityResult(
            ingestion_log_id=log.id,
            valid_records=len(valid_records),
            invalid_records=invalid_count,
            duplicate_records=duplicate_count,
            missing_value_records=0,
        )
        db.add(quality)

        log.status = "success" if invalid_count == 0 else "partial"
        log.finished_at = datetime.now(timezone.utc)
        db.commit()
        logger.info(
            f"Customer ingestion: fetched={log.records_fetched}, ingested={log.records_ingested}, "
            f"invalid={invalid_count}, duplicates={duplicate_count}"
        )

    except Exception as e:
        db.rollback()
        log.status = "failed"
        log.error_message = str(e)
        log.finished_at = datetime.now(timezone.utc)
        db.add(log)
        db.commit()
        logger.error(f"Customer ingestion failed: {e}")
        raise

    return log


def ingest_products(db: Session) -> DataIngestionLog:
    """
    Ingests product catalog records. Products change rarely, so this is
    typically a small, fast, low-risk ingestion.
    """
    log = DataIngestionLog(source="products", status="failed", records_fetched=0, records_ingested=0)
    db.add(log)
    db.flush()

    try:
        raw_products = generate_products(count=40)
        log.records_fetched = len(raw_products)

        existing_ids = {row[0] for row in db.query(Product.external_id).all()}
        new_products = [
            Product(**p) for p in raw_products if p["external_id"] not in existing_ids
        ]
        db.add_all(new_products)
        log.records_ingested = len(new_products)

        quality = DataQualityResult(
            ingestion_log_id=log.id,
            valid_records=len(raw_products),
            invalid_records=0,
            duplicate_records=len(raw_products) - len(new_products),
            missing_value_records=0,
        )
        db.add(quality)

        log.status = "success"
        log.finished_at = datetime.now(timezone.utc)
        db.commit()
        logger.info(f"Product ingestion: fetched={log.records_fetched}, ingested={log.records_ingested}")

    except Exception as e:
        db.rollback()
        log.status = "failed"
        log.error_message = str(e)
        log.finished_at = datetime.now(timezone.utc)
        db.add(log)
        db.commit()
        logger.error(f"Product ingestion failed: {e}")
        raise

    return log


def ingest_orders(db: Session) -> DataIngestionLog:
    """
    Ingests order records, incrementally: only considers orders placed
    after our last successful orders ingestion, demonstrating incremental
    ingestion rather than reprocessing the full history every time.
    """
    log = DataIngestionLog(source="orders", status="failed", records_fetched=0, records_ingested=0)
    db.add(log)
    db.flush()

    try:
        since_date = _get_last_successful_ingestion_date(db, "orders")

        # We need customers/products (by external_id) to build FK lookups.
        # In a real system, these would already exist from prior CRM/product
        # ingestion; here we re-fetch the same deterministic mock data to
        # resolve external_id -> internal id mappings.
        raw_customers = fetch_customers(limit=500)
        raw_products = generate_products(count=40)

        raw_orders = fetch_orders(raw_customers, raw_products, days=180)

        if since_date:
            raw_orders = [
                o for o in raw_orders
                if datetime.fromisoformat(o["order_date"]) > since_date
            ]

        log.records_fetched = len(raw_orders)

        # --- Schema validation step (Phase 8) ---
        valid_orders = []
        invalid_count = 0
        for o in raw_orders:
            try:
                validated = OrderRecordSchema(**o)
                valid_orders.append(validated.model_dump())
            except ValidationError as ve:
                invalid_count += 1
                logger.warning(f"Rejected invalid order record {o.get('external_id')}: {ve.errors()}")
        raw_orders = valid_orders  # only validated records proceed
        # --- end validation step ---

                # Track schema-invalid and FK-invalid separately for accurate metrics
        schema_invalid_count = invalid_count  # count so far, before FK check

        existing_ids = {row[0] for row in db.query(Order.external_id).all()}
        customer_map = {c.external_id: c.id for c in db.query(Customer).all()}
        product_map = {p.external_id: p.id for p in db.query(Product).all()}

        new_orders = []
        fk_invalid_count = 0
        for o in raw_orders:
            if o["external_id"] in existing_ids:
                continue
            if o["customer_external_id"] not in customer_map or o["product_external_id"] not in product_map:
                fk_invalid_count += 1
                continue
            new_orders.append(Order(
                external_id=o["external_id"],
                customer_id=customer_map[o["customer_external_id"]],
                product_id=product_map[o["product_external_id"]],
                quantity=o["quantity"],
                total_amount=o["total_amount"],
                status=o["status"],
                region=o["region"],
                channel=o["channel"],
                order_date=datetime.fromisoformat(o["order_date"]),
            ))

        total_invalid_count = schema_invalid_count + fk_invalid_count
        duplicate_count = len(raw_orders) - len(new_orders) - fk_invalid_count

        db.add_all(new_orders)
        log.records_ingested = len(new_orders)

        quality = DataQualityResult(
            ingestion_log_id=log.id,
            valid_records=len(new_orders),
            invalid_records=total_invalid_count,
            duplicate_records=duplicate_count,
            missing_value_records=0,
        )
        db.add(quality)

        log.status = "success" if total_invalid_count == 0 else "partial"
        log.finished_at = datetime.now(timezone.utc)
        db.commit()
        logger.info(
            f"Order ingestion: fetched={log.records_fetched}, ingested={log.records_ingested}, "
            f"invalid={total_invalid_count}"
        )
    except Exception as e:
        db.rollback()
        log.status = "failed"
        log.error_message = str(e)
        log.finished_at = datetime.now(timezone.utc)
        db.add(log)
        db.commit()
        logger.error(f"Order ingestion failed: {e}")
        raise

    return log


def ingest_marketing(db: Session) -> DataIngestionLog:
    """
    Ingests marketing campaigns and their spend records.
    """
    log = DataIngestionLog(source="marketing", status="failed", records_fetched=0, records_ingested=0)
    db.add(log)
    db.flush()

    try:
        raw_campaigns = fetch_campaigns(count=8)

        existing_campaign_ids = {row[0] for row in db.query(MarketingCampaign.external_id).all()}
        new_campaigns = [
            MarketingCampaign(**c) for c in raw_campaigns if c["external_id"] not in existing_campaign_ids
        ]
        db.add_all(new_campaigns)
        db.flush()

        campaign_map = {c.external_id: c.id for c in db.query(MarketingCampaign).all()}

        raw_spend = fetch_marketing_spend(raw_campaigns, days=180)
        log.records_fetched = len(raw_spend)

        # Marketing spend has no natural external_id, so we treat
        # (campaign_id, spend_date) as the uniqueness key for dedup.
        existing_spend_keys = {
            (row[0], row[1]) for row in db.query(MarketingSpend.campaign_id, MarketingSpend.spend_date).all()
        }

        new_spend = []
        for s in raw_spend:
            campaign_id = campaign_map[s["campaign_external_id"]]
            spend_date = datetime.fromisoformat(s["spend_date"]).date()
            if (campaign_id, spend_date) in existing_spend_keys:
                continue
            new_spend.append(MarketingSpend(
                campaign_id=campaign_id,
                spend_date=spend_date,
                amount=s["amount"],
            ))

        db.add_all(new_spend)
        log.records_ingested = len(new_spend)

        quality = DataQualityResult(
            ingestion_log_id=log.id,
            valid_records=len(raw_spend),
            invalid_records=0,
            duplicate_records=len(raw_spend) - len(new_spend),
            missing_value_records=0,
        )
        db.add(quality)

        log.status = "success"
        log.finished_at = datetime.now(timezone.utc)
        db.commit()
        logger.info(f"Marketing ingestion: fetched={log.records_fetched}, ingested={log.records_ingested}")

    except Exception as e:
        db.rollback()
        log.status = "failed"
        log.error_message = str(e)
        log.finished_at = datetime.now(timezone.utc)
        db.add(log)
        db.commit()
        logger.error(f"Marketing ingestion failed: {e}")
        raise

    return log


def run_full_ingestion(db: Session) -> dict:
    """
    Orchestrates all four ingestion steps in the correct dependency order:
    customers and products must exist before orders (FK dependency),
    campaigns must exist before spend.
    """
    results = {}
    results["customers"] = ingest_customers(db)
    results["products"] = ingest_products(db)
    results["orders"] = ingest_orders(db)
    results["marketing"] = ingest_marketing(db)
    return results
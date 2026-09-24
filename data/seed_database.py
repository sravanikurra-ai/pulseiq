"""
One-time (or re-runnable) script to seed the database with synthetic data.
Run manually from the backend's virtual environment:
    python -m data.seed_database
"""
import sys
from pathlib import Path
from datetime import datetime

# Allow importing from backend/app when running this script from project root
sys.path.append(str(Path(__file__).resolve().parents[1] / "backend"))

from app.db.session import SessionLocal
from app.models import Customer, Product, Order, MarketingCampaign, MarketingSpend

from data.mock_apis.crm_api import fetch_customers
from data.mock_apis.orders_api import fetch_orders
from data.mock_apis.marketing_api import fetch_campaigns, fetch_marketing_spend


def seed():
    db = SessionLocal()
    try:
        print("Fetching mock customers...")
        raw_customers = fetch_customers(limit=500)
        customers = [Customer(**c) for c in raw_customers]
        db.add_all(customers)
        db.commit()
        print(f"  Inserted {len(customers)} customers.")

        print("Fetching mock products...")
        from data.generators.products import generate_products
        raw_products = generate_products(count=40)
        products = [Product(**p) for p in raw_products]
        db.add_all(products)
        db.commit()
        print(f"  Inserted {len(products)} products.")

        print("Fetching mock orders...")
        raw_orders = fetch_orders(raw_customers, raw_products, days=180)

        # Build lookup maps from external_id -> real DB id, since orders
        # reference customers/products by external_id but the DB needs
        # the actual internal foreign key (integer id).
        customer_map = {c.external_id: c.id for c in customers}
        product_map = {p.external_id: p.id for p in products}

        order_objs = []
        for o in raw_orders:
            order_objs.append(Order(
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
        db.add_all(order_objs)
        db.commit()
        print(f"  Inserted {len(order_objs)} orders.")

        print("Fetching mock marketing campaigns...")
        raw_campaigns = fetch_campaigns(count=8)
        campaigns = [MarketingCampaign(**c) for c in raw_campaigns]
        db.add_all(campaigns)
        db.commit()
        print(f"  Inserted {len(campaigns)} campaigns.")

        print("Fetching mock marketing spend...")
        raw_spend = fetch_marketing_spend(raw_campaigns, days=180)
        campaign_map = {c.external_id: c.id for c in campaigns}
        spend_objs = [
            MarketingSpend(
                campaign_id=campaign_map[s["campaign_external_id"]],
                spend_date=datetime.fromisoformat(s["spend_date"]).date(),
                amount=s["amount"],
            )
            for s in raw_spend
        ]
        db.add_all(spend_objs)
        db.commit()
        print(f"  Inserted {len(spend_objs)} marketing spend records.")

        print("\nSeeding complete.")

    except Exception as e:
        db.rollback()
        print(f"Seeding failed, rolled back: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
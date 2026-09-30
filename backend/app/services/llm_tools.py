"""
The controlled tool layer for the LLM analytics assistant (Phase 17).

CRITICAL DESIGN RULE: every function here wraps an EXISTING, already-tested
deterministic service (kpi_engine, anomaly_service, forecast_service). None
of these functions write raw SQL or accept SQL from the LLM. The LLM can
only choose WHICH of these to call and with WHICH arguments — never HOW
they're implemented. This is what prevents hallucinated numbers: the LLM
never computes a metric, it only receives one we already computed.
"""
from datetime import date, timedelta
from sqlalchemy.orm import Session

from app.services import kpi_engine
from app.models import Anomaly, Forecast


def get_revenue(db: Session, start_date: str, end_date: str) -> dict:
    start, end = date.fromisoformat(start_date), date.fromisoformat(end_date)
    return {"metric": "revenue", "start": start_date, "end": end_date,
            "value": kpi_engine.calculate_revenue(db, start, end)}

def get_average_daily_revenue(db: Session, start_date: str, end_date: str) -> dict:
    start, end = date.fromisoformat(start_date), date.fromisoformat(end_date)
    total = kpi_engine.calculate_revenue(db, start, end)
    days = (end - start).days + 1
    return {
        "metric": "average_daily_revenue", "start": start_date, "end": end_date,
        "total_revenue": total, "days": days,
        "value": round(total / days, 2) if days > 0 else 0.0,
    }


def get_orders(db: Session, start_date: str, end_date: str) -> dict:
    start, end = date.fromisoformat(start_date), date.fromisoformat(end_date)
    return {"metric": "orders", "start": start_date, "end": end_date,
            "value": kpi_engine.calculate_orders(db, start, end)}


def get_aov(db: Session, start_date: str, end_date: str) -> dict:
    start, end = date.fromisoformat(start_date), date.fromisoformat(end_date)
    return {"metric": "aov", "start": start_date, "end": end_date,
            "value": kpi_engine.calculate_aov(db, start, end)}


def get_growth_rate(db: Session, start_date: str, end_date: str) -> dict:
    start, end = date.fromisoformat(start_date), date.fromisoformat(end_date)
    return {"metric": "growth_rate", "start": start_date, "end": end_date,
            "value": kpi_engine.calculate_growth_rate(db, start, end),
            "note": "Compares this period's revenue to the immediately preceding period of equal length."}


def get_marketing_roi(db: Session, start_date: str, end_date: str) -> dict:
    start, end = date.fromisoformat(start_date), date.fromisoformat(end_date)
    return {"metric": "marketing_roi", "start": start_date, "end": end_date,
            "value": kpi_engine.calculate_marketing_roi(db, start, end),
            "note": kpi_engine.KPI_LIMITATIONS["marketing_roi"]}


def get_recent_anomalies(db: Session, limit: int = 5) -> dict:
    rows = db.query(Anomaly).order_by(Anomaly.detected_at.desc()).limit(limit).all()
    return {"anomalies": [
        {"date": a.detected_at.date().isoformat(), "metric": a.metric_name,
         "observed": float(a.observed_value), "expected": float(a.expected_value) if a.expected_value else None,
         "explanation": a.explanation}
        for a in rows
    ]}


def get_forecast(db: Session, limit: int = 7) -> dict:
    rows = db.query(Forecast).order_by(Forecast.forecast_date.asc()).limit(limit).all()
    return {"forecasts": [
        {"date": f.forecast_date.isoformat(), "predicted_value": float(f.predicted_value),
         "lower_bound": float(f.lower_bound) if f.lower_bound else None,
         "upper_bound": float(f.upper_bound) if f.upper_bound else None,
         "model": f.model_name}
        for f in rows
    ]}


# --- Tool registry: name -> (function, JSON schema for the LLM) ---
TOOLS = {
    "get_revenue": {
        "fn": get_revenue,
        "schema": {
            "type": "function",
            "function": {
                "name": "get_revenue",
                "description": "Get total completed-order revenue for a date range.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "start_date": {"type": "string", "description": "YYYY-MM-DD"},
                        "end_date": {"type": "string", "description": "YYYY-MM-DD"},
                    },
                    "required": ["start_date", "end_date"],
                },
            },
        },
    },
        "get_average_daily_revenue": {
        "fn": get_average_daily_revenue,
        "schema": {
            "type": "function",
            "function": {
                "name": "get_average_daily_revenue",
                "description": "Get average revenue PER DAY for a date range (total revenue divided by number of days). Use this instead of manually dividing get_revenue's total.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "start_date": {"type": "string", "description": "YYYY-MM-DD"},
                        "end_date": {"type": "string", "description": "YYYY-MM-DD"},
                    },
                    "required": ["start_date", "end_date"],
                },
            },
        },
    },
    "get_orders": {
        "fn": get_orders,
        "schema": {
            "type": "function",
            "function": {
                "name": "get_orders",
                "description": "Get the count of completed orders for a date range.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "start_date": {"type": "string", "description": "YYYY-MM-DD"},
                        "end_date": {"type": "string", "description": "YYYY-MM-DD"},
                    },
                    "required": ["start_date", "end_date"],
                },
            },
        },
    },
    "get_aov": {
        "fn": get_aov,
        "schema": {
            "type": "function",
            "function": {
                "name": "get_aov",
                "description": "Get average order value (revenue / orders) for a date range.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "start_date": {"type": "string", "description": "YYYY-MM-DD"},
                        "end_date": {"type": "string", "description": "YYYY-MM-DD"},
                    },
                    "required": ["start_date", "end_date"],
                },
            },
        },
    },
    "get_growth_rate": {
        "fn": get_growth_rate,
        "schema": {
            "type": "function",
            "function": {
                "name": "get_growth_rate",
                "description": "Get revenue growth rate (%) for a period vs. the immediately preceding period of equal length.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "start_date": {"type": "string", "description": "YYYY-MM-DD"},
                        "end_date": {"type": "string", "description": "YYYY-MM-DD"},
                    },
                    "required": ["start_date", "end_date"],
                },
            },
        },
    },
    "get_marketing_roi": {
        "fn": get_marketing_roi,
        "schema": {
            "type": "function",
            "function": {
                "name": "get_marketing_roi",
                "description": "Get aggregate marketing ROI (%) for a date range: (revenue - spend) / spend.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "start_date": {"type": "string", "description": "YYYY-MM-DD"},
                        "end_date": {"type": "string", "description": "YYYY-MM-DD"},
                    },
                    "required": ["start_date", "end_date"],
                },
            },
        },
    },
    "get_recent_anomalies": {
        "fn": get_recent_anomalies,
        "schema": {
            "type": "function",
            "function": {
                "name": "get_recent_anomalies",
                "description": "Get the most recently detected anomalies in daily order patterns.",
                "parameters": {
                    "type": "object",
                    "properties": {"limit": {"type": "integer", "description": "Max results, default 5"}},
                    "required": [],
                },
            },
        },
    },
    "get_forecast": {
        "fn": get_forecast,
        "schema": {
            "type": "function",
            "function": {
                "name": "get_forecast",
                "description": "Get upcoming revenue forecast values.",
                "parameters": {
                    "type": "object",
                    "properties": {"limit": {"type": "integer", "description": "Max results, default 7"}},
                    "required": [],
                },
            },
        },
    },
}
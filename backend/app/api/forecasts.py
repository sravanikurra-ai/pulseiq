from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.forecast_service import generate_forecast
from app.models import Forecast
from app.api.deps import require_role
router = APIRouter(prefix="/forecasts", tags=["Forecasts"], dependencies=[Depends(require_role("VIEWER"))])



@router.post("/run", dependencies=[Depends(require_role("ANALYST"))])
async def trigger_forecast(db: Session = Depends(get_db)):
    return generate_forecast(db)


@router.get("/")
async def list_forecasts(db: Session = Depends(get_db)):
    results = db.query(Forecast).order_by(Forecast.forecast_date.asc()).all()
    return [
        {
            "id": f.id,
            "metric_name": f.metric_name,
            "forecast_date": f.forecast_date.isoformat(),
            "predicted_value": float(f.predicted_value),
            "lower_bound": float(f.lower_bound) if f.lower_bound is not None else None,
            "upper_bound": float(f.upper_bound) if f.upper_bound is not None else None,
            "model_name": f.model_name,
            "mae": float(f.mae) if f.mae is not None else None,
        }
        for f in results
    ]
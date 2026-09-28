"""
Forecasting service (Phase 12).

WHAT PROBLEM THIS SOLVES: predicts near-future daily revenue, so the
business can anticipate rather than only react.

WHY NOT DEEP LEARNING: with ~180 days of data, a statistical baseline is
more appropriate and more explainable than a deep learning model, which
typically needs much more data to reliably outperform simpler methods.

MODEL SELECTION: a model's error only means something relative to a
baseline. We compared Holt exponential smoothing against simpler methods
(naive, moving average, no-trend smoothing, damped trend), first on one
held-out window and then across six rolling windows. The best methods
were statistically tied, so the production model is the simplest of them:
a 14-day moving average.

KNOWN LIMITATION: the forecast is flat. The planted growth trend is small
relative to daily noise, so no method tested can exploit it at a 14-day
horizon. The interval width is also constant across the horizon.
"""
import logging
from datetime import timedelta
import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from sqlalchemy.orm import Session
from sqlalchemy import func as sql_func

from app.models import FactOrdersDaily, Forecast

logger = logging.getLogger(__name__)

MODEL_NAME = "moving_average_14d"
MA_WINDOW = 14
TEST_SIZE_DAYS = 14         # held-out days for the single-window evaluation
FORECAST_HORIZON_DAYS = 14  # how far into the future we predict


def _load_daily_revenue(db: Session) -> pd.DataFrame:
    rows = (
        db.query(
            FactOrdersDaily.order_date,
            sql_func.sum(FactOrdersDaily.total_revenue).label("total_revenue"),
        )
        .filter(FactOrdersDaily.status == "completed")
        .group_by(FactOrdersDaily.order_date)
        .order_by(FactOrdersDaily.order_date)
        .all()
    )
    df = pd.DataFrame(rows, columns=["order_date", "total_revenue"])
    df["total_revenue"] = df["total_revenue"].astype(float)
    return df


def _metrics(actual: np.ndarray, predicted: np.ndarray) -> dict:
    return {
        "mae": round(float(np.mean(np.abs(actual - predicted))), 2),
        "rmse": round(float(np.sqrt(np.mean((actual - predicted) ** 2))), 2),
    }


def _evaluate_on_holdout(train_series: pd.Series, test_series: pd.Series) -> dict:
    """
    Trains on the past, tests on the held-out final days (chronological
    split, never shuffled). Compares candidate methods on one window.
    The top-level mae/rmse/mape describe Holt's additive trend model
    (a leftover from the first version); trust `comparison` and
    `rolling_origin` for model selection.
    """
    n = len(test_series)
    actual = test_series.values

    holt = ExponentialSmoothing(
        train_series, trend="add", seasonal=None, initialization_method="estimated"
    ).fit()
    holt_pred = holt.forecast(n).values

    ses = ExponentialSmoothing(
        train_series, trend=None, seasonal=None, initialization_method="estimated"
    ).fit()

    damped = ExponentialSmoothing(
        train_series, trend="add", damped_trend=True, seasonal=None,
        initialization_method="estimated",
    ).fit()

    candidates = {
        "holt_additive_trend": holt_pred,
        "simple_exp_smoothing_no_trend": ses.forecast(n).values,
        "holt_damped_trend": damped.forecast(n).values,
        "naive_last_value": np.repeat(train_series.iloc[-1], n),
        "moving_average_14d": np.repeat(train_series.iloc[-MA_WINDOW:].mean(), n),
    }
    comparison = {name: _metrics(actual, pred) for name, pred in candidates.items()}

    # MAPE for Holt, flagged unreliable if any actual is near zero
    nonzero_mask = actual > 1.0
    if nonzero_mask.sum() > 0:
        mape = float(np.mean(
            np.abs((actual[nonzero_mask] - holt_pred[nonzero_mask]) / actual[nonzero_mask])
        ) * 100)
        mape_reliable = bool(nonzero_mask.sum() == len(actual))
    else:
        mape, mape_reliable = None, False

    main = _metrics(actual, holt_pred)
    return {
        "mae": main["mae"],
        "rmse": main["rmse"],
        "mape": round(mape, 2) if mape is not None else None,
        "mape_reliable": mape_reliable,
        "test_size_days": n,
        "comparison": comparison,
    }


def _candidate_forecasts(train: pd.Series, n: int) -> dict:
    """Fits every candidate method on `train` and forecasts `n` days ahead."""
    holt = ExponentialSmoothing(
        train, trend="add", seasonal=None, initialization_method="estimated"
    ).fit()
    ses = ExponentialSmoothing(
        train, trend=None, seasonal=None, initialization_method="estimated"
    ).fit()
    damped = ExponentialSmoothing(
        train, trend="add", damped_trend=True, seasonal=None,
        initialization_method="estimated",
    ).fit()
    return {
        "holt_additive_trend": holt.forecast(n).values,
        "simple_exp_smoothing": ses.forecast(n).values,
        "holt_damped_trend": damped.forecast(n).values,
        "naive_last_value": np.repeat(train.iloc[-1], n),
        "moving_average_14d": np.repeat(train.iloc[-MA_WINDOW:].mean(), n),
    }


def _rolling_origin_comparison(series: pd.Series, n_windows: int = 6, horizon: int = 14) -> dict:
    """
    Repeats the chronological train/test split at several cut-off points
    and averages the errors, so the model ranking doesn't hinge on one
    lucky or unlucky window.
    """
    errors = {}
    for k in range(n_windows, 0, -1):
        cut = len(series) - k * horizon
        train = series.iloc[:cut]
        test = series.iloc[cut:cut + horizon].values
        for name, pred in _candidate_forecasts(train, horizon).items():
            err = test - pred
            bucket = errors.setdefault(name, {"mae": [], "rmse": []})
            bucket["mae"].append(float(np.mean(np.abs(err))))
            bucket["rmse"].append(float(np.sqrt(np.mean(err ** 2))))

    return {
        name: {
            "mean_mae": round(float(np.mean(v["mae"])), 2),
            "mean_rmse": round(float(np.mean(v["rmse"])), 2),
            "mae_std_across_windows": round(float(np.std(v["mae"])), 2),
        }
        for name, v in errors.items()
    }


def generate_forecast(db: Session) -> dict:
    df = _load_daily_revenue(db)

    if len(df) < TEST_SIZE_DAYS + 30:
        return {
            "status": "skipped",
            "reason": "insufficient_data",
            "rows_available": len(df),
            "minimum_required": TEST_SIZE_DAYS + 30,
        }

    series = pd.Series(df["total_revenue"].values, index=pd.DatetimeIndex(df["order_date"]))

    # --- Evaluation: single holdout window, plus rolling windows if enough history ---
    train = series.iloc[:-TEST_SIZE_DAYS]
    test = series.iloc[-TEST_SIZE_DAYS:]
    evaluation = _evaluate_on_holdout(train, test)
    if len(series) >= 6 * 14 + 30:
        evaluation["rolling_origin"] = _rolling_origin_comparison(series)

    # --- Production forecast: flat 14-day moving average (no trend claimed) ---
    forecast_value = float(series.iloc[-MA_WINDOW:].mean())

    # Uncertainty from this method's own one-step-ahead errors on history.
    # Empirical 2.5% / 97.5% quantiles: robust to the planted spike/crash days.
    trailing_mean = series.rolling(MA_WINDOW).mean().shift(1)
    errors = (series - trailing_mean).dropna()
    lower_err = float(np.quantile(errors, 0.025))
    upper_err = float(np.quantile(errors, 0.975))

    # MAE recorded with the forecast = this method's rolling-window mean MAE
    model_mae = (
        evaluation.get("rolling_origin", {}).get("moving_average_14d", {}).get("mean_mae")
        or evaluation["comparison"]["moving_average_14d"]["mae"]
    )

    # Idempotency: clear previous forecasts before inserting fresh ones
    db.query(Forecast).filter(Forecast.metric_name == "daily_revenue").delete(synchronize_session=False)
    db.commit()

    forecast_rows = []
    last_date = df["order_date"].iloc[-1]
    for i in range(1, FORECAST_HORIZON_DAYS + 1):
        forecast_date = last_date + timedelta(days=i)
        lower = round(max(forecast_value + lower_err, 0), 2)
        upper = round(forecast_value + upper_err, 2)

        db.add(Forecast(
            metric_name="daily_revenue",
            forecast_date=forecast_date,
            predicted_value=round(forecast_value, 2),
            lower_bound=lower,
            upper_bound=upper,
            model_name=MODEL_NAME,
            mae=model_mae,
        ))
        forecast_rows.append({
            "date": forecast_date.isoformat(),
            "predicted_value": round(forecast_value, 2),
            "lower_bound": lower,
            "upper_bound": upper,
        })

    db.commit()
    logger.info(f"Forecast generated with {MODEL_NAME}: mean rolling MAE={model_mae}")

    return {
        "status": "success",
        "model_name": MODEL_NAME,
        "model_selection_note": (
            "Chosen via rolling-origin comparison of 5 methods; moving_average_14d tied for best "
            "and is the simplest. Forecast is flat: the underlying growth trend is too small "
            "relative to daily noise to be exploited at a 14-day horizon."
        ),
        "evaluation": evaluation,
        "forecast_horizon_days": FORECAST_HORIZON_DAYS,
        "forecasts": forecast_rows,
    }
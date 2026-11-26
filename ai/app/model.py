import os

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

MODEL_PATH = os.getenv("MODEL_PATH", "models/model.joblib")
_model = None


def generate_sample(days: int = 14, seed: int = 42, anomaly_rate: float = 0.02) -> pd.DataFrame:
    """Consommation horaire synthetique : cycle journalier + bruit + anomalies injectees."""
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2026-01-01", periods=days * 24, freq="h")
    hours = idx.hour.values
    base = 0.6 + 0.9 * np.exp(-((hours - 8) ** 2) / 8) + 1.3 * np.exp(-((hours - 20) ** 2) / 10)
    kwh = base + rng.normal(0, 0.08, len(idx))
    n_anom = max(1, int(len(idx) * anomaly_rate))
    pos = rng.choice(len(idx), n_anom, replace=False)
    for i, p in enumerate(pos):
        kwh[p] = kwh[p] * rng.uniform(3, 5) if i % 2 == 0 else 0.0  # pic ou coupure
    return pd.DataFrame({"timestamp": idx, "kwh": np.clip(kwh, 0, None)})


def features(df: pd.DataFrame) -> np.ndarray:
    ts = pd.to_datetime(df["timestamp"])
    return np.column_stack([df["kwh"].values, ts.dt.hour.values, ts.dt.dayofweek.values])


def train(df: pd.DataFrame, contamination: float = 0.02) -> IsolationForest:
    global _model
    model = IsolationForest(n_estimators=200, contamination=contamination, random_state=42)
    model.fit(features(df))
    os.makedirs(os.path.dirname(MODEL_PATH) or ".", exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    _model = model
    return model


def get_model() -> IsolationForest:
    global _model
    if _model is None:
        if os.path.exists(MODEL_PATH):
            _model = joblib.load(MODEL_PATH)
        else:
            _model = train(generate_sample())
    return _model


def predict(df: pd.DataFrame) -> list[dict]:
    model = get_model()
    X = features(df)
    labels = model.predict(X)  # -1 = anomalie
    scores = -model.decision_function(X)  # plus grand = plus anormal
    return [
        {"timestamp": str(t), "is_anomaly": bool(l == -1), "score": float(s)}
        for t, l, s in zip(df["timestamp"], labels, scores)
    ]

from datetime import datetime

import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from . import model as ml

app = FastAPI(title="Isolation Forest service", version="1.0.0")


class Reading(BaseModel):
    timestamp: datetime
    kwh: float


class Batch(BaseModel):
    readings: list[Reading]


def to_df(batch: Batch) -> pd.DataFrame:
    return pd.DataFrame([r.model_dump() for r in batch.readings])


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/sample")
def sample(days: int = 14):
    df = ml.generate_sample(days=days)
    return {
        "readings": [
            {"timestamp": t.isoformat(), "kwh": round(float(k), 4)}
            for t, k in zip(df["timestamp"], df["kwh"])
        ]
    }


@app.post("/train")
def train(batch: Batch, contamination: float = 0.02):
    if len(batch.readings) < 50:
        raise HTTPException(400, "Au moins 50 mesures requises")
    ml.train(to_df(batch), contamination)
    return {"trained_on": len(batch.readings)}


@app.post("/predict")
def predict(batch: Batch):
    if not batch.readings:
        raise HTTPException(400, "Aucune mesure")
    return {"results": ml.predict(to_df(batch))}

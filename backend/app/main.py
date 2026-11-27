import csv
import io
import time
from contextlib import asynccontextmanager
from datetime import datetime

import httpx
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from . import ai_client, models, schemas
from .database import Base, engine, get_db


def init_db(retries: int = 30, delay: float = 2.0):
    """MySQL peut demarrer apres le backend : on reessaie."""
    for attempt in range(retries):
        try:
            Base.metadata.create_all(bind=engine)
            return
        except Exception as exc:  # noqa: BLE001
            print(f"[db] pas prete ({attempt + 1}/{retries}): {exc}")
            time.sleep(delay)
    raise RuntimeError("Base de donnees injoignable")


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="Power Anomaly API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


@app.get("/api/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok"}


def _insert(db: Session, items: list[schemas.ReadingIn]) -> int:
    db.add_all(
        [models.Reading(ts=i.timestamp.replace(tzinfo=None), kwh=i.kwh) for i in items]
    )
    db.commit()
    return len(items)


@app.post("/api/readings")
def add_readings(items: list[schemas.ReadingIn], db: Session = Depends(get_db)):
    return {"inserted": _insert(db, items)}


@app.post("/api/readings/upload")
async def upload_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """CSV avec en-tetes : timestamp,kwh"""
    content = (await file.read()).decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(content))
    items = []
    try:
        for row in reader:
            items.append(
                schemas.ReadingIn(
                    timestamp=datetime.fromisoformat(row["timestamp"].strip()),
                    kwh=float(row["kwh"]),
                )
            )
    except (KeyError, ValueError) as exc:
        raise HTTPException(400, f"CSV invalide (timestamp,kwh attendus): {exc}")
    return {"inserted": _insert(db, items)}


@app.get("/api/readings", response_model=list[schemas.ReadingOut])
def list_readings(limit: int = 2000, db: Session = Depends(get_db)):
    rows = (
        db.query(models.Reading).order_by(models.Reading.ts.desc()).limit(limit).all()
    )
    return list(reversed(rows))


@app.delete("/api/readings")
def reset(db: Session = Depends(get_db)):
    deleted = db.query(models.Reading).delete()
    db.commit()
    return {"deleted": deleted}


@app.post("/api/demo")
def load_demo(db: Session = Depends(get_db)):
    try:
        sample = ai_client.ai_sample()
    except httpx.HTTPError as exc:
        raise HTTPException(502, f"Service IA indisponible: {exc}")
    items = [schemas.ReadingIn(**r) for r in sample]
    return {"inserted": _insert(db, items)}


@app.post("/api/detect")
def detect(db: Session = Depends(get_db)):
    rows = db.query(models.Reading).order_by(models.Reading.ts).all()
    if not rows:
        raise HTTPException(400, "Aucune mesure a analyser")
    payload = [{"timestamp": r.ts.isoformat(), "kwh": r.kwh} for r in rows]
    try:
        results = ai_client.ai_predict(payload)
    except httpx.HTTPError as exc:
        raise HTTPException(502, f"Service IA indisponible: {exc}")
    for row, res in zip(rows, results):
        row.is_anomaly = bool(res["is_anomaly"])
        row.score = float(res["score"])
    db.commit()
    return {"analysed": len(rows), "anomalies": sum(1 for r in rows if r.is_anomaly)}


@app.get("/api/anomalies", response_model=list[schemas.ReadingOut])
def anomalies(db: Session = Depends(get_db)):
    return (
        db.query(models.Reading)
        .filter(models.Reading.is_anomaly.is_(True))
        .order_by(models.Reading.score.desc())
        .all()
    )


@app.get("/api/stats", response_model=schemas.Stats)
def stats(db: Session = Depends(get_db)):
    total = db.query(func.count(models.Reading.id)).scalar() or 0
    n = (
        db.query(func.count(models.Reading.id))
        .filter(models.Reading.is_anomaly.is_(True))
        .scalar()
        or 0
    )
    return schemas.Stats(
        total=total, anomalies=n, anomaly_rate=round(n / total, 4) if total else 0.0
    )

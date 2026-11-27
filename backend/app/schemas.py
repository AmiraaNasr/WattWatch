from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ReadingIn(BaseModel):
    timestamp: datetime
    kwh: float


class ReadingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ts: datetime
    kwh: float
    is_anomaly: bool
    score: Optional[float] = None


class Stats(BaseModel):
    total: int
    anomalies: int
    anomaly_rate: float

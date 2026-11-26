import os
import httpx

AI_URL = os.getenv("AI_URL", "http://ai:8001")


def ai_predict(readings: list[dict]) -> list[dict]:
    """readings: [{"timestamp": iso, "kwh": float}] -> [{"timestamp","is_anomaly","score"}]"""
    r = httpx.post(f"{AI_URL}/predict", json={"readings": readings}, timeout=60)
    r.raise_for_status()
    return r.json()["results"]


def ai_sample() -> list[dict]:
    r = httpx.get(f"{AI_URL}/sample", timeout=60)
    r.raise_for_status()
    return r.json()["readings"]

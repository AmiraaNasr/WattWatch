import os

os.environ["DATABASE_URL"] = "sqlite:///./test.db"

from fastapi.testclient import TestClient  # noqa: E402

from app import ai_client  # noqa: E402
from app.main import app  # noqa: E402


def fake_predict(readings):
    return [
        {"timestamp": r["timestamp"], "is_anomaly": r["kwh"] > 10, "score": r["kwh"] / 10}
        for r in readings
    ]


def test_full_flow(monkeypatch):
    monkeypatch.setattr(ai_client, "ai_predict", fake_predict)
    with TestClient(app) as c:
        c.delete("/api/readings")
        assert c.get("/api/health").json() == {"status": "ok"}

        data = [
            {"timestamp": "2026-01-01T00:00:00", "kwh": 1.2},
            {"timestamp": "2026-01-01T01:00:00", "kwh": 1.1},
            {"timestamp": "2026-01-01T02:00:00", "kwh": 42.0},
        ]
        assert c.post("/api/readings", json=data).json() == {"inserted": 3}

        r = c.post("/api/detect")
        assert r.status_code == 200 and r.json()["anomalies"] == 1

        anomalies = c.get("/api/anomalies").json()
        assert len(anomalies) == 1 and anomalies[0]["kwh"] == 42.0

        s = c.get("/api/stats").json()
        assert s["total"] == 3 and s["anomalies"] == 1


def test_csv_upload_invalid():
    with TestClient(app) as c:
        r = c.post("/api/readings/upload", files={"file": ("x.csv", b"a,b\n1,2\n")})
        assert r.status_code == 400

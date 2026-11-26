import os

os.environ["MODEL_PATH"] = "/tmp/test_model.joblib"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_spike_is_detected():
    readings = client.get("/sample").json()["readings"]
    readings[-1]["kwh"] = 60.0  # pic evident
    res = client.post("/predict", json={"readings": readings}).json()["results"]
    assert len(res) == len(readings)
    assert res[-1]["is_anomaly"] is True


def test_predict_empty():
    assert client.post("/predict", json={"readings": []}).status_code == 400

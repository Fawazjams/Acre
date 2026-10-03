"""API tests for the Acre cloud service. Runs against a throwaway SQLite file."""
import os
import tempfile
import uuid

_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()
os.environ["ACRE_DATABASE_URL"] = f"sqlite:///{_tmp.name}"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from cloud.app.main import app  # noqa: E402


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:  # context manager runs the startup hook (init_db)
        yield c


def _batch(det_uuid: str, sensor_uuid: str) -> dict:
    return {
        "device_id": "pi-test",
        "records": {
            "detections": [{
                "uuid": det_uuid,
                "zone_id": "zone-a",
                "captured_at": "2026-06-20T12:00:00Z",
                "type": "disease",
                "class_name": "Tomato___Early_blight",
                "confidence": 0.91,
                "health_score": 42.0,
                "led_state": "red",
            }],
            "sensor_readings": [{
                "uuid": sensor_uuid,
                "zone_id": "zone-a",
                "captured_at": "2026-06-20T12:00:00Z",
                "temperature_c": 24.5,
                "humidity_pct": 61.0,
            }],
        },
    }


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "service": "acre-cloud"}


def test_sync_ingests_new_records(client):
    r = client.post("/api/sync", json=_batch(str(uuid.uuid4()), str(uuid.uuid4())))
    assert r.status_code == 200
    assert r.json() == {"synced": 2, "duplicates_ignored": 0}


def test_sync_is_idempotent(client):
    payload = _batch(str(uuid.uuid4()), str(uuid.uuid4()))
    first = client.post("/api/sync", json=payload).json()
    retry = client.post("/api/sync", json=payload).json()
    assert first == {"synced": 2, "duplicates_ignored": 0}
    assert retry == {"synced": 0, "duplicates_ignored": 2}


def test_sync_rejects_malformed_payload(client):
    r = client.post("/api/sync", json={"device_id": "pi-test"})
    assert r.status_code == 422


def test_map_for_unknown_farm_is_empty(client):
    r = client.get("/api/farms/does-not-exist/map")
    assert r.status_code == 200
    assert r.json()["zones"] == []

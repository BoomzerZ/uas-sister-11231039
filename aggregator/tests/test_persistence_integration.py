import os
import time
import requests
import pytest

BASE = os.getenv("AGG_URL", "http://localhost:8080")

def test_persistence_across_restart():
    payload = {
        "topic": "persist",
        "event_id": "persist-1",
        "timestamp": "2025-01-01T00:00:00Z",
        "source": "pytest",
        "payload": {"x": 1},
    }

    r1 = requests.post(f"{BASE}/publish", json=payload)
    assert r1.status_code == 200

    # bring down storage container and restart (manual step / scripted)
    # Here we assume external test harness will restart compose, or run the test
    # after a compose restart. For simple automation, user can run:
    # docker compose down && docker compose up -d storage && sleep 3

    # verify event still in DB and not reprocessed when resent
    r2 = requests.post(f"{BASE}/publish", json=payload)
    assert r2.status_code == 200

    stats = requests.get(f"{BASE}/stats").json()
    assert stats["unique_processed"] == 1

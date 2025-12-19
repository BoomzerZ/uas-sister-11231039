import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_publish_and_dedup():
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test"
    ) as ac:

        payload = {
            "topic": "test",
            "event_id": "evt-1",
            "timestamp": "2025-01-01T00:00:00Z",
            "source": "pytest",
            "payload": {"x": 1},
        }

        r1 = await ac.post("/publish", json=payload)
        r2 = await ac.post("/publish", json=payload)

        assert r1.status_code == 200
        assert r2.status_code == 200

        stats = (await ac.get("/stats")).json()
        assert stats["unique_processed"] == 1
        assert stats["duplicate_dropped"] == 1

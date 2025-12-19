import asyncio
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_concurrent_publish_dedup():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Prepare 50 unique ids, each duplicated 3x => total 150 posts
        ids = [f"evt-{i}" for i in range(50)]
        payloads = []
        for eid in ids:
            payload = {
                "topic": "concurrent",
                "event_id": eid,
                "timestamp": "2025-01-01T00:00:00Z",
                "source": "pytest",
                "payload": {"x": 1},
            }
            payloads += [payload]*3

        async def do_post(p):
            return await ac.post("/publish", json=p)

        results = await asyncio.gather(*[do_post(p) for p in payloads])
        # all requests return 200
        assert all(r.status_code == 200 for r in results)

        stats = (await ac.get("/stats")).json()
        assert stats["unique_processed"] == 50
        assert stats["duplicate_dropped"] == 100

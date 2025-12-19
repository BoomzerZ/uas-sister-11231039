import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_publish_schema_missing_field():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        invalid = {"topic": "t", "timestamp": "2025-01-01T00:00:00Z", "payload": {}}
        r = await ac.post("/publish", json=invalid)
        assert r.status_code == 422  # fastapi/pydantic validation

from fastapi import APIRouter, HTTPException
from typing import List, Union
from .schemas import Event
from .db import get_pool
import json
from datetime import datetime

router = APIRouter()

@router.post("/publish")
async def publish(events: Union[Event, List[Event]]):
    if isinstance(events, Event):
        events = [events]

    pool = await get_pool()
    results = []

    async with pool.acquire() as conn:
        # Process events one by one inside their own transaction
        for ev in events:
            # normalize timestamp to ISO/datetimes if needed
            ts = ev.timestamp if hasattr(ev, "timestamp") else datetime.utcnow()
            payload_json = json.dumps(ev.payload)

            async with conn.transaction():
                # try insert; if conflict -> no row returned
                inserted = await conn.fetchval(
                    """
                    INSERT INTO processed_events (topic, event_id, timestamp, source, payload)
                    VALUES ($1, $2, $3, $4, $5::jsonb)
                    ON CONFLICT (topic, event_id) DO NOTHING
                    RETURNING event_id
                    """,
                    ev.topic,
                    ev.event_id,
                    ts,
                    ev.source,
                    payload_json
                )

                # always increment received
                await conn.execute(
                    "UPDATE stats SET received = received + 1 WHERE id = 1"
                )

                if inserted:
                    # new unique processed event
                    await conn.execute(
                        "UPDATE stats SET unique_processed = unique_processed + 1 WHERE id = 1"
                    )
                    results.append({"event_id": ev.event_id, "status": "processed"})
                else:
                    # duplicate
                    await conn.execute(
                        "UPDATE stats SET duplicate_dropped = duplicate_dropped + 1 WHERE id = 1"
                    )
                    results.append({"event_id": ev.event_id, "status": "duplicate"})

    return {"results": results, "count": len(results)}


@router.get("/events")
async def get_events(topic: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT topic, event_id, timestamp, source, payload FROM processed_events WHERE topic = $1 ORDER BY timestamp",
            topic
        )
    return [dict(r) for r in rows]


@router.get("/stats")
async def stats():
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM stats WHERE id = 1")
    return dict(row)

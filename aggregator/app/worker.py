import asyncio
import os
import json
import redis.asyncio as redis
from .db import get_pool

BROKER_URL = os.getenv("BROKER_URL", "redis://broker:6379/0")
WORKER_COUNT = int(os.getenv("WORKER_COUNT", 2))

async def worker(name: str):
    r = redis.from_url(BROKER_URL)
    pool = await get_pool()
    print(f"[{name}] started, connecting to broker {BROKER_URL}")

    while True:
        try:
            item = await r.blpop("event_queue", timeout=0)  # blocking
            if not item:
                await asyncio.sleep(0.1)
                continue

            # item is (queue_name, raw_bytes)
            _, raw = item
            if isinstance(raw, bytes):
                raw = raw.decode()
            event = json.loads(raw)

            async with pool.acquire() as conn:
                async with conn.transaction():
                    inserted = await conn.fetchval(
                        """
                        INSERT INTO processed_events (topic, event_id, timestamp, source, payload)
                        VALUES ($1, $2, $3, $4, $5::jsonb)
                        ON CONFLICT (topic, event_id) DO NOTHING
                        RETURNING event_id
                        """,
                        event["topic"],
                        event["event_id"],
                        event.get("timestamp"),
                        event.get("source", "worker"),
                        json.dumps(event.get("payload", {}))
                    )

                    await conn.execute("UPDATE stats SET received = received + 1 WHERE id = 1")
                    if inserted:
                        await conn.execute("UPDATE stats SET unique_processed = unique_processed + 1 WHERE id = 1")
                        print(f"[{name}] processed {event['event_id']}")
                    else:
                        await conn.execute("UPDATE stats SET duplicate_dropped = duplicate_dropped + 1 WHERE id = 1")
                        print(f"[{name}] duplicate {event['event_id']}")

        except Exception as e:
            print(f"[{name}] error: {e}")
            await asyncio.sleep(1)


async def start_workers():
    # launch N concurrent workers
    await asyncio.gather(*[worker(f"W{i}") for i in range(WORKER_COUNT)])

if __name__ == "__main__":
    asyncio.run(start_workers())

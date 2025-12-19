import pytest_asyncio
import asyncpg
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:pass@storage:5432/db"
)

@pytest_asyncio.fixture(autouse=True)
async def reset_db():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        # bersihkan event yang sudah diproses
        await conn.execute(
            "TRUNCATE processed_events RESTART IDENTITY CASCADE;"
        )

        # reset statistik
        await conn.execute(
            """
            UPDATE stats
            SET received = 0,
                unique_processed = 0,
                duplicate_dropped = 0
            WHERE id = 1
            """
        )
    finally:
        await conn.close()

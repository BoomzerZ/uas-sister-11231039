from fastapi import FastAPI
from .api import router
import asyncio
from .worker import start_workers
import os

TESTING = os.getenv("TESTING", "0") == "1"

app = FastAPI(title="Distributed Log Aggregator")
app.include_router(router)


@app.on_event("startup")
async def startup():
    if not TESTING:
        # hanya jalankan worker saat BUKAN testing
        asyncio.create_task(start_workers())

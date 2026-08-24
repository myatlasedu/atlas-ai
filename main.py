from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from api.routes.ai import router as ai_router

from middleware import (
    RequestLockMiddleware
)

from db.session import (
    AsyncSessionLocal,
)


@asynccontextmanager
async def lifespan(app):

    #
    # Warm the database connection pool BEFORE the first
    # real user arrives. SELECT 1 is the cheapest possible
    # query; it forces every pool connection to open now
    # instead of letting request #1 pay a multi-second
    # cold-start bill. If the database happens to be down
    # at boot we still start - the pool will build lazily.
    #

    try:

        async with AsyncSessionLocal() as session:

            await session.execute(text("SELECT 1"))

        print("Database pool warmed up.")

    except Exception as exc:

        print(f"Database warmup skipped: {exc}")

    yield


app = FastAPI(
    title="ERP AI Copilot",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# app.add_middleware(RequestLockMiddleware)

app.include_router(
    ai_router,
    prefix="/api/ai",
    tags=["AI"]
)


@app.get("/health")
async def health_check():

    return {
        "status": "ok"
    }
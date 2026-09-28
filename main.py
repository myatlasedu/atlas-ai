import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.ai import router as ai_router
from services.intent_classifier import MiniLMIntentClassifier

from middleware import RequestLockMiddleware

from api.routes.chat_session import (
    router as chat_session_router
)

from middleware import (
    RequestLockMiddleware
)

from cache.redis import redis_client
from core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):

    app.state.intent_classifier = MiniLMIntentClassifier(
        model_dir="models/student-intent-v4-onnx",
        intra_op_threads=2,
    )

    yield

    app.state.intent_classifier = None



logger = logging.getLogger(__name__)

# AI service's Redis connection pool closes when the FastAPI app shuts down. This is important because
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        yield
    finally:
        await redis_client.close()

app = FastAPI(
    title="ERP AI Copilot",
    version="1.0.0",
    lifespan=lifespan,
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
    tags=["AI"],
)

if settings.session_api_enabled:

    logger.warning(
        "Chat session API is ENABLED (APP_ENV=%s). "
        "This must not be used in production.",
        settings.APP_ENV,
    )

    app.include_router(
        chat_session_router,
        prefix="/api/ai",
        tags=["AI Sessions (non-production only)"]
    )

else:

    logger.info(
        "Chat session API is disabled (APP_ENV=%s).",
        settings.APP_ENV,
    )


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
    }
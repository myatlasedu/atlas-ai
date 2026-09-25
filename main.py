import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.ai import router as ai_router
from api.routes.chat_session import (
    router as chat_session_router
)

from middleware import (
    RequestLockMiddleware
)

from core.config import settings


logger = logging.getLogger(__name__)


app = FastAPI(
    title="ERP AI Copilot",
    version="1.0.0",
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
        "status": "ok"
    }
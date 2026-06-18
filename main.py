from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.ai import router as ai_router

from middleware import (
    RequestLockMiddleware
)


app = FastAPI(
    title="ERP AI Copilot",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestLockMiddleware)

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
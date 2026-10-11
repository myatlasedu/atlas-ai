import uuid
import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from cache.redis_cache import RedisCache


logger = logging.getLogger(__name__)

lock_cache = RedisCache(
    prefix="atlas_ai_lock"
)

class RequestLockMiddleware(
    BaseHTTPMiddleware
):

    async def dispatch(
        self,
        request: Request,
        call_next
    ):

        if request.url.path != "/api/ai/query":

            return await call_next(
                request
            )

        try:

            body = await request.json()

            context = body.get(
                "context"
            )

        except Exception:

            return await call_next(
                request
            )

        if not context:

            return await call_next(
                request
            )

        user_id = context.get("user_id")

        if user_id is None:

            return await call_next(
                request
            )

        request_id = str(
            uuid.uuid4()
        )

        lock_key = str(user_id)

        # ==========================================
        # ACQUIRE LOCK
        # ==========================================

        try:
            acquired = await lock_cache.set_if_not_exists(
                lock_key,
                request_id,
                expire=120
            )

        except Exception as exc:
            logger.warning(
                "Request lock skipped (redis unavailable): %s",
                exc,
            )

            return await call_next(
                request
            )

        if not acquired:

            return JSONResponse(
                status_code=409,
                content={
                    "success": False,
                    "message": (
                        "Another AI request is "
                        "already being processed."
                    )
                }
            )

        try:

            # ==========================================
            # PROCESS REQUEST
            # ==========================================

            response = await call_next(
                request
            )

            return response

        finally:

            # ==========================================
            # RELEASE LOCK
            # ==========================================

            try:
                await lock_cache.delete_if_value_matches(
                    lock_key,
                    request_id,
                )

            except Exception as exc:
                logger.warning(
                    "Request lock cleanup skipped "
                    "(redis unavailable): %s",
                    exc,
                )
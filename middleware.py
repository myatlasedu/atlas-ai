import uuid

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from cache.redis import redis_client


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

        user_id = context["user_id"]

        request_id = str(
            uuid.uuid4()
        )

        lock_key = (
            f"atlas_ai_lock:{user_id}"
        )

        acquired = await redis_client.set(

            lock_key,

            request_id,

            ex=120,

            nx=True
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

            response = await call_next(
                request
            )

            return response

        finally:

            current_value = (
                await redis_client.get(
                    lock_key
                )
            )

            if (
                current_value
                and
                current_value
                == request_id
            ):

                await redis_client.delete(
                    lock_key
                )
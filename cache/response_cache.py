import hashlib
import json
import logging

from cache.redis import (
    redis_client,
)

from utils import (
    ist_today,
    is_guardian_context,
)

logger = logging.getLogger(__name__)

TTL_SECONDS = 300


class ResponseCache:

    @staticmethod
    def _build_key(
        context,
        query,
        rev: int = 0,
        session_marker: str | None = None,
    ) -> str:

        qhash = (
            hashlib
            .sha256(
                query
                .strip()
                .lower()
                .encode(
                    "utf-8"
                )
            )
            .hexdigest()
        )

        user_id = getattr(
            context,
            "user_id",
            "none",
        )

        role = getattr(
            context,
            "role",
            "none",
        )

        if is_guardian_context(context):

            role = "guardian"

        student_id = getattr(
            context,
            "student_id",
            "none",
        )

        campus_id = getattr(
            context,
            "campus_id",
            "none",
        )

        extra = (
            getattr(
                context,
                "staff_id",
                None,
            )
            or
            getattr(
                context,
                "academic_year_id",
                None,
            )
        )

        marker = (
            session_marker
            if session_marker
            else "none"
        )

        return (
            f"cache:{user_id}:{role}:"
            f"{student_id}:{campus_id}:{extra}:"
            f"{marker}:{rev}:{qhash}:{ist_today()}"
        )

    @staticmethod
    async def get(
        context,
        query,
        rev: int = 0,
        session_marker: str | None = None,
    ):

        key = (
            ResponseCache._build_key(
                context,
                query,
                rev,
                session_marker,
            )
        )

        try:

            raw = (
                await redis_client.get(
                    key
                )
            )

            if raw is None:

                return None

            return (
                json.loads(
                    raw
                )
            )

        except Exception:

            logger.exception(
                "ResponseCache.get failed"
            )

            return None

    @staticmethod
    async def set(
        context,
        query,
        response,
        rev: int = 0,
        session_marker: str | None = None,
    ):

        key = (
            ResponseCache._build_key(
                context,
                query,
                rev,
                session_marker,
            )
        )

        try:

            await redis_client.set(
                key,
                json.dumps(
                    response,
                    default=str,
                ),
                ex=TTL_SECONDS,
            )

        except Exception:

            logger.exception(
                "ResponseCache.set failed"
            )
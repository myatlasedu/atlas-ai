import json
import logging

from cache.redis_cache import RedisCache

from db.repositories.ai_conversation_audit_repository import (
    make_json_safe,
)

logger = logging.getLogger(__name__)


class SessionMemoryCache:
    TTL_SECONDS = 60 * 60 * 24  # 24 hours
    MAX_RECORDS = 20

    cache = RedisCache(
        prefix="ai_session_memory"
    )

    # ==================================================
    # READ
    # ==================================================

    @classmethod
    async def load(
        cls,
        session_id,
    ) -> list[dict] | None:

        if not session_id:
            return None

        key = str(session_id)

        try:
            raw = await cls.cache.get(
                key
            )

            if raw is None:
                return None

            # Reading counts as activity.
            await cls.cache.expire(
                key,
                cls.TTL_SECONDS,
            )

        except Exception as exc:
            logger.warning(
                "Session memory read skipped (redis unavailable): %s",
                exc,
            )

            return None

        try:
            records = json.loads(
                raw
            )

        except (ValueError, TypeError):
            logger.warning(
                "Discarding malformed session memory for session=%s",
                session_id,
            )

            return None

        return (
            records
            if isinstance(records, list)
            else None
        )

    # ==================================================
    # WRITE
    # ==================================================

    @classmethod
    async def save(
        cls,
        session_id,
        records: list[dict],
    ) -> None:

        if not session_id:
            return

        payload = json.dumps(
            make_json_safe(
                records[-cls.MAX_RECORDS:]
            )
        )

        try:
            await cls.cache.set(
                str(session_id),
                payload,
                expire=cls.TTL_SECONDS,
            )

        except Exception as exc:
            logger.warning(
                "Session memory save skipped (redis unavailable): %s",
                exc,
            )

    # ==================================================
    # DELETE
    # ==================================================

    @classmethod
    async def clear(
        cls,
        session_id,
    ) -> None:

        if not session_id:
            return

        try:
            await cls.cache.delete(
                str(session_id)
            )

        except Exception as exc:
            logger.warning(
                "Session memory delete skipped (redis unavailable): %s",
                exc,
            )
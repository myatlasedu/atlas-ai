import json
import logging

from cache.redis import (
    redis_client,
)

from db.repositories.ai_conversation_audit_repository import (
    make_json_safe,
)

logger = logging.getLogger(__name__)


class SessionMemoryCache:

    PREFIX = "ai_session_memory"

    TTL_SECONDS = (
        60 * 60 * 24
    )

    MAX_RECORDS = 20

    @classmethod
    def _key(
        cls,
        session_id,
    ) -> str:

        return (
            f"{cls.PREFIX}:{session_id}"
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

        key = cls._key(
            session_id
        )

        try:

            raw = await redis_client.get(
                key
            )

            if raw is None:

                return None


            await redis_client.expire(
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

        key = cls._key(
            session_id
        )

        payload = json.dumps(
            make_json_safe(
                records[-cls.MAX_RECORDS:]
            )
        )

        try:

            await redis_client.set(
                key,
                payload,
                ex=cls.TTL_SECONDS,
            )

        except Exception as exc:

            logger.warning(
                "Session memory save skipped (redis unavailable): %s",
                exc,
            )

    @classmethod
    async def clear(
        cls,
        session_id,
    ) -> None:

        if not session_id:

            return

        try:

            await redis_client.delete(
                cls._key(
                    session_id
                )
            )

        except Exception as exc:

            logger.warning(
                "Session memory delete skipped (redis unavailable): %s",
                exc,
            )

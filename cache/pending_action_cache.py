import json
import logging

from cache.redis_cache import RedisCache

logger = logging.getLogger(__name__)

class PendingActionCache:
    TTL_SECONDS = 60 * 15  # 15 minutes

    cache = RedisCache(
        prefix="pending_action"
    )

    @classmethod
    async def save(
        cls,
        user_id: int,
        action_type: str,
        payload: dict,
        session_id: int | None = None,
    ):
        if session_id is None:
            return

        value = {
            "action_type": action_type,
            "payload": payload,
        }

        try:
            await cls.cache.set(
                f"{session_id}:{user_id}",
                json.dumps(value),
                expire=cls.TTL_SECONDS,
            )

            logger.info(
                "Pending action saved for user=%s session=%s",
                user_id,
                session_id,
            )

        except Exception as exc:
            logger.warning(
                "Pending action save skipped (redis unavailable): %s",
                exc,
            )

    @classmethod
    async def get(
        cls,
        user_id: int,
        session_id: int | None = None,
    ):
        if session_id is None:
            return None

        try:
            value = await cls.cache.get(
                f"{session_id}:{user_id}"
            )

        except Exception as exc:
            logger.warning(
                "Pending action read skipped (redis unavailable): %s",
                exc,
            )
            return None

        if not value:
            return None

        try:
            return json.loads(value)

        except json.JSONDecodeError as exc:
            logger.warning(
                "Invalid pending action cache value for session=%s: %s",
                session_id,
                exc,
            )
            return None

    @classmethod
    async def delete(
        cls,
        user_id: int,
        session_id: int | None = None,
    ):
        if session_id is None:
            return

        try:
            await cls.cache.delete(
                f"{session_id}:{user_id}"
            )

            logger.info(
                "Pending action deleted for user=%s session=%s",
                user_id,
                session_id,
            )

        except Exception as exc:
            logger.warning(
                "Pending action delete skipped (redis unavailable): %s",
                exc,
            )
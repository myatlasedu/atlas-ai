import json
import logging

from cache.redis import (
    redis_client
)

logger = logging.getLogger(__name__)


class PendingActionCache:

    PREFIX = "pending_action"

    TTL_SECONDS = (
        60 * 15
    )

    @classmethod
    def _key(
        cls,
        user_id,
        session_id,
    ) -> str | None:

        if not session_id or user_id is None:

            return None

        return (
            f"{cls.PREFIX}:{user_id}:{session_id}"
        )

    @classmethod
    async def save(
        cls,
        user_id: int,
        action_type: str,
        payload: dict,
        session_id=None,
    ):

        key = cls._key(
            user_id,
            session_id,
        )

        if key is None:

            logger.warning(
                "Pending action not saved: no session for user=%s",
                user_id,
            )

            return

        value = {

            "action_type":
                action_type,

            "payload":
                payload
        }

        try:

            await redis_client.set(

                key,

                json.dumps(value),

                ex=cls.TTL_SECONDS
            )

            logger.info(
                "Pending action saved for user=%s session=%s",
                user_id,
                session_id,
            )

        except Exception as exc:

            logger.warning(
                "Pending action save skipped (redis unavailable): %s",
                exc
            )

    @classmethod
    async def get(
        cls,
        user_id: int,
        session_id=None,
    ):

        key = cls._key(
            user_id,
            session_id,
        )

        if key is None:

            return None

        try:

            value = await redis_client.get(
                key
            )

        except Exception as exc:

            logger.warning(
                "Pending action read skipped (redis unavailable): %s",
                exc
            )

            return None

        if not value:

            return None

        return json.loads(
            value
        )

    @classmethod
    async def delete(
        cls,
        user_id: int,
        session_id=None,
    ):

        key = cls._key(
            user_id,
            session_id,
        )

        if key is None:

            return

        try:

            await redis_client.delete(
                key
            )

            logger.info(
                "Pending action deleted for user=%s session=%s",
                user_id,
                session_id,
            )

        except Exception as exc:

            logger.warning(
                "Pending action delete skipped (redis unavailable): %s",
                exc
            )

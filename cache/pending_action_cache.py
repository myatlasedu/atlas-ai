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
    async def save(
        cls,
        user_id: int,
        action_type: str,
        payload: dict
    ):

        key = (
            f"{cls.PREFIX}:{user_id}"
        )

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
                "Pending action saved for user=%s",
                user_id
            )

        except Exception as exc:

            #
            # Redis unavailable: the conversation must keep
            # flowing. Only the confirmation round-trip is
            # lost for this turn.
            #

            logger.warning(
                "Pending action save skipped (redis unavailable): %s",
                exc
            )

    @classmethod
    async def get(
        cls,
        user_id: int
    ):

        key = (
            f"{cls.PREFIX}:{user_id}"
        )

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
        user_id: int
    ):

        key = (
            f"{cls.PREFIX}:{user_id}"
        )

        try:

            await redis_client.delete(
                key
            )

            logger.info(
                "Pending action deleted for user=%s",
                user_id
            )

        except Exception as exc:

            logger.warning(
                "Pending action delete skipped (redis unavailable): %s",
                exc
            )
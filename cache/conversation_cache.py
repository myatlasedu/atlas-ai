import json
import logging

from cache.redis import (
    redis_client
)

from db.repositories.ai_conversation_audit_repository import (
    AIConversationAuditRepository,
    make_json_safe,
)

logger = logging.getLogger(__name__)


class ConversationCache:

    PREFIX = "ai_conversation"

    TTL_SECONDS = (
        60 * 60 * 24
    )

    MAX_TURNS = 5

    @classmethod
    def _key(
        cls,
        session_id,
    ) -> str:

        return (
            f"{cls.PREFIX}:{session_id}"
        )

    @classmethod
    def is_contextual(
        cls,
        predicted_intent,
    ) -> bool:

        # Confirmations and unparseable queries tell the next
        # turn nothing, so they never enter the cache.

        return (
            str(
                predicted_intent
                or ""
            ).lower()
            not in
            AIConversationAuditRepository.NON_CONTEXTUAL_INTENTS
        )

    # ==================================================
    # WRITE
    # ==================================================

    @classmethod
    async def append(
        cls,
        session_id,
        turn: dict,
    ) -> None:

        if not session_id:

            return

        if not cls.is_contextual(
            turn.get(
                "predicted_intent"
            )
        ):

            return

        key = cls._key(
            session_id
        )

        try:

            pipeline = redis_client.pipeline()

            # Newest first, matching the order the DB fallback
            # returns and the order intent parsing expects.

            pipeline.lpush(
                key,
                json.dumps(
                    make_json_safe(
                        turn
                    )
                ),
            )

            pipeline.ltrim(
                key,
                0,
                cls.MAX_TURNS - 1,
            )

            pipeline.expire(
                key,
                cls.TTL_SECONDS,
            )

            await pipeline.execute()

        except Exception as exc:

            # Redis unavailable: the next turn simply rebuilds
            # its context from Postgres.

            logger.warning(
                "Conversation cache append skipped (redis unavailable): %s",
                exc,
            )

    @classmethod
    async def seed(
        cls,
        session_id,
        turns: list[dict],
    ) -> None:

        # Replaces whatever is cached with the turns just read
        # back from Postgres. Called when a session resumes
        # after the key has expired.

        if not session_id:

            return

        key = cls._key(
            session_id
        )

        payload = [
            json.dumps(
                make_json_safe(
                    turn
                )
            )
            for turn in turns[: cls.MAX_TURNS]
        ]

        try:

            pipeline = redis_client.pipeline()

            pipeline.delete(
                key
            )

            if payload:

                # turns arrive newest first and rpush preserves
                # that order.

                pipeline.rpush(
                    key,
                    *payload,
                )

                pipeline.expire(
                    key,
                    cls.TTL_SECONDS,
                )

            await pipeline.execute()

            logger.info(
                "Seeded %s turn(s) into conversation cache for session=%s",
                len(payload),
                session_id,
            )

        except Exception as exc:

            logger.warning(
                "Conversation cache seed skipped (redis unavailable): %s",
                exc,
            )

    # ==================================================
    # READ
    # ==================================================

    @classmethod
    async def load(
        cls,
        session_id,
        limit: int | None = None,
    ) -> list[dict] | None:

        #
        # None  -> nothing cached, the caller must rebuild.
        # []    -> cached and genuinely empty.
        #

        if not session_id:

            return None

        key = cls._key(
            session_id
        )

        try:

            exists = await redis_client.exists(
                key
            )

            if not exists:

                return None

            raw = await redis_client.lrange(
                key,
                0,
                (
                    limit
                    or cls.MAX_TURNS
                ) - 1,
            )

            # Reading counts as activity, so an active session
            # never expires mid-conversation.

            await redis_client.expire(
                key,
                cls.TTL_SECONDS,
            )

        except Exception as exc:

            logger.warning(
                "Conversation cache read skipped (redis unavailable): %s",
                exc,
            )

            return None

        turns = []

        for item in raw:

            try:

                turns.append(
                    json.loads(
                        item
                    )
                )

            except (ValueError, TypeError):

                logger.warning(
                    "Discarding malformed cached turn for session=%s",
                    session_id,
                )

        return turns

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
                "Conversation cache delete skipped (redis unavailable): %s",
                exc,
            )

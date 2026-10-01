import json
import logging

from cache.redis_cache import RedisCache

from db.repositories.ai_conversation_audit_repository import (
    AIConversationAuditRepository,
    make_json_safe,
)

logger = logging.getLogger(__name__)


class ConversationCache:
    TTL_SECONDS = 60 * 60 * 24  # 24 hours
    MAX_TURNS = 5

    cache = RedisCache(
        prefix="ai_conversation"
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
                predicted_intent or ""
            ).lower()
            not in AIConversationAuditRepository.NON_CONTEXTUAL_INTENTS
        )

    # ==================================================
    # WRITE
    # ==================================================

    @classmethod
    async def seed(
        cls,
        session_id,
        turns: list[dict],
    ) -> None:

        # Replaces whatever is cached with the turns just read
        # back from Postgres.
        if not session_id:
            return

        payload = [
            json.dumps(
                make_json_safe(turn)
            )
            for turn in turns[:cls.MAX_TURNS]
        ]

        try:
            await cls.cache.replace_list_with_ttl(
                str(session_id),
                payload,
                expire=cls.TTL_SECONDS,
            )

            logger.info(
                "Seeded %s cached turn(s) for session=%s",
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

        if not session_id:
            return None

        key = str(session_id)

        try:
            exists = await cls.cache.exists(
                key
            )

            if not exists:
                return None

            max_turns = (
                cls.MAX_TURNS
                if limit is None
                else limit
            )

            raw = await cls.cache.lrange(
                key,
                0,
                max_turns - 1,
            )

            # Reading counts as activity, so an active session
            # never expires mid-conversation.
            await cls.cache.expire(
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
                    json.loads(item)
                )

            except (ValueError, TypeError):
                logger.warning(
                    "Discarding malformed cached turn for session=%s",
                    session_id,
                )

        return turns

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
                "Conversation cache delete skipped (redis unavailable): %s",
                exc,
            )
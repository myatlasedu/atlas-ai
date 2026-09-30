import json
import logging

from cache.redis_cache import RedisCache

from db.repositories.ai_conversation_audit_repository import (
    make_json_safe,
)

logger = logging.getLogger(__name__)


class ConversationRecallCache:
    TTL_SECONDS = 60 * 60 * 24 * 7  # 7 days
    MAX_ENTRIES = 20

    cache = RedisCache(
        prefix="ai_conversation_recall"
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
            exists = await cls.cache.exists(
                key
            )

            if not exists:
                return None

            raw = await cls.cache.lrange(
                key,
                0,
                cls.MAX_ENTRIES - 1,
            )

            # Reading counts as activity.
            await cls.cache.expire(
                key,
                cls.TTL_SECONDS,
            )

        except Exception as exc:
            logger.warning(
                "Conversation recall cache read skipped (redis unavailable): %s",
                exc,
            )

            return None

        entries = []

        for item in raw:
            try:
                entries.append(
                    json.loads(item)
                )

            except (ValueError, TypeError):
                logger.warning(
                    "Discarding malformed recall entry for session=%s",
                    session_id,
                )

        return entries

    # ==================================================
    # WRITE
    # ==================================================

    @classmethod
    async def append(
        cls,
        session_id,
        *,
        user_query: str,
        chatbot_summary: str,
    ) -> None:

        if not session_id:
            return

        entry = json.dumps(
            make_json_safe(
                {
                    "user_query": user_query,
                    "chatbot_summary": chatbot_summary,
                }
            )
        )

        key = str(session_id)

        try:
            await cls.cache.rpush(
                key,
                entry,
            )

            # Trim to keep only the latest MAX_ENTRIES.
            await cls.cache.ltrim(
                key,
                -cls.MAX_ENTRIES,
                -1,
            )

            await cls.cache.expire(
                key,
                cls.TTL_SECONDS,
            )

        except Exception as exc:
            logger.warning(
                "Conversation recall cache append skipped (redis unavailable): %s",
                exc,
            )

    @classmethod
    async def seed(
        cls,
        session_id,
        entries: list[dict],
    ) -> None:

        if not session_id:
            return

        payload = [
            json.dumps(
                make_json_safe(entry)
            )
            for entry in entries[-cls.MAX_ENTRIES:]
        ]

        try:
            await cls.cache.replace_list_with_ttl(
                str(session_id),
                payload,
                expire=cls.TTL_SECONDS,
            )

            logger.info(
                "Seeded %s recall entry(ies) for session=%s",
                len(payload),
                session_id,
            )

        except Exception as exc:
            logger.warning(
                "Conversation recall cache seed skipped (redis unavailable): %s",
                exc,
            )

    # ==================================================
    # REBUILD FROM DB
    # ==================================================

    @classmethod
    async def rebuild_from_db(
        cls,
        session_id,
    ) -> list[dict]:

        if not session_id:
            return []

        from db.repositories.ai_chat_session_repository import (
            AIChatSessionRepository,
        )

        from db.session import AsyncSessionLocal

        try:

            async with AsyncSessionLocal() as db:

                rows = await AIChatSessionRepository().list_recall_turns(
                    db,
                    session_id=session_id,
                )

        except Exception:

            logger.exception(
                "Failed to rebuild conversation recall cache; "
                "continuing without it."
            )

            return []

        if not rows:

            logger.info(
                "No prior recall turns for session=%s; "
                "treating as new session.",
                session_id,
            )

            return []

        logger.info(
            "Rebuilt %s recall entry(ies) from ai_chat_message "
            "for session=%s",
            len(rows),
            session_id,
        )

        await cls.seed(
            session_id,
            rows,
        )

        return rows

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
                "Conversation recall cache delete skipped (redis unavailable): %s",
                exc,
            )

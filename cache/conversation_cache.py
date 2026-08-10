import json
import logging

from cache.redis import (
    redis_client,
)

from core.config import (
    settings,
)

from utils import (
    is_guardian_context,
)

from schemas.conversation import (
    ConversationSession,
    ConversationTurn,
)

logger = logging.getLogger(__name__)


class ConversationCache:

    PREFIX = "conv"

    TTL_SECONDS = settings.CONVERSATION_TTL_SECONDS

    MAX_TURNS = settings.CONVERSATION_MAX_TURNS

    @staticmethod
    def scope_key(context) -> str:

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
            None,
        )

        if student_id is None:

            student_id = "none"

        return (
            f"{ConversationCache.PREFIX}:"
            f"{user_id}:{role}:{student_id}"
        )

    @classmethod
    async def get(
        cls,
        scope_key: str,
    ) -> ConversationSession | None:

        try:

            raw = await redis_client.get(
                scope_key
            )

            if raw is None:

                return None

            return ConversationSession.model_validate(
                json.loads(raw)
            )

        except Exception:

            logger.exception(
                "ConversationCache.get failed for key=%s",
                scope_key,
            )

            return None

    @classmethod
    async def save(
        cls,
        scope_key: str,
        session: ConversationSession,
    ):

        try:

            await redis_client.set(
                scope_key,
                json.dumps(
                    session.model_dump(mode="json")
                ),
                ex=cls.TTL_SECONDS,
            )

        except Exception:

            logger.exception(
                "ConversationCache.save failed for key=%s",
                scope_key,
            )

    @classmethod
    async def delete(
        cls,
        scope_key: str,
    ):

        try:

            await redis_client.delete(
                scope_key
            )

        except Exception:

            logger.exception(
                "ConversationCache.delete failed for key=%s",
                scope_key,
            )

    @classmethod
    async def add_turn(
        cls,
        scope_key: str,
        session: ConversationSession | None,
        turn: ConversationTurn,
    ):

        if session is None:

            logger.warning(
                "ConversationCache.add_turn called with no session for key=%s",
                scope_key,
            )

            return None

        if session.turns is None:

            session.turns = []

        session.turns.append(
            turn
        )

        session.turns = (
            session.turns[-cls.MAX_TURNS:]
        )

        session.current_intent = (
            turn.intent
        )

        session.rev += 1

        await cls.save(
            scope_key,
            session,
        )

        return session

import logging

from services.chat_session_service import (
    current_turn,
)

from cache.conversation_recall_cache import (
    ConversationRecallCache,
)


logger = logging.getLogger(__name__)


class ConversationRecallTool:

    async def run(
        self,
        context,
        parsed_intent,
    ):

        turn = current_turn.get()

        session_id = getattr(
            turn,
            "session_id",
            None,
        )

        scope = (
            getattr(
                parsed_intent,
                "recall_scope",
                None,
            )
            or "summary"
        )

        # ==============================================
        # LOAD FROM CACHE (OR REBUILD)
        # ==============================================

        entries = await ConversationRecallCache.load(
            session_id,
        )

        if entries is None:
            entries = await ConversationRecallCache.rebuild_from_db(
                session_id,
            )

        logger.info(
            "Conversation recall: scope=%s entries=%s",
            scope,
            len(entries),
        )

        # ==============================================
        # EMPTY SESSION
        # ==============================================

        if not entries:

            return {
                "module": "conversation_recall",
                "direct_answer": (
                    "As per my memory, this is the start of our "
                    "conversation and you haven't asked me "
                    "anything yet."
                ),
            }

        # ==============================================
        # SCOPE: ASKED
        # ==============================================

        if scope == "asked":

            asked_entries = [
                entry.get("user_query")
                for entry in entries
                if entry.get("user_query")
            ]

            if not asked_entries:

                return {
                    "module": "conversation_recall",
                    "direct_answer": (
                        "As per my memory, you haven't asked me "
                        "anything in this conversation yet."
                    ),
                }

        # ==============================================
        # RETURN CONTEXT FOR SUMMARIZER
        # ==============================================

        return {
            "module": "conversation_recall",
            "llm_context": {
                "scope": scope,
                "conversation": list(
                    reversed(entries)
                ),
            },
        }

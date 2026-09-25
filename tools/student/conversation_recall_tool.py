import logging

from services.chat_session_service import (
    current_turn,
)

from services.context_service import (
    ConversationContextService,
)

from services.session_memory_service import (
    SessionMemoryService,
    STATUS_CANCELLED,
    STATUS_COMPLETED,
    STATUS_PENDING,
)


logger = logging.getLogger(__name__)

MAX_ANSWER_CHARS = 300

STATUS_LABELS = {
    STATUS_COMPLETED: "saved",
    STATUS_PENDING: "proposed but not confirmed yet",
    STATUS_CANCELLED: "cancelled by the student",
}


class ConversationRecallTool:

    async def run(
        self,
        context,
        parsed_intent,
    ):

        turn = current_turn.get()

        scope = (
            getattr(
                parsed_intent,
                "recall_scope",
                None,
            )
            or "summary"
        )

        actions = await SessionMemoryService.load(
            turn=turn,
        )

        turns = await ConversationContextService.load_recent_turns(
            session_id=turn.session_id,
        )

        # The cache is newest first; a recap reads better in order.

        turns = list(
            reversed(
                turns
            )
        )

        logger.info(
            "Conversation recall: scope=%s actions=%s turns=%s",
            scope,
            len(actions),
            len(turns),
        )

        direct_answer = self._empty_answer(
            scope=scope,
            actions=actions,
            turns=turns,
        )

        if direct_answer:

            return {
                "module": "conversation_recall",
                "direct_answer": direct_answer,
            }


        llm_context = {
            "scope": scope,
        }

        if scope != "asked":

            llm_context["actions"] = [
                self._action_line(
                    position,
                    record,
                )
                for position, record in enumerate(
                    actions,
                    start=1,
                )
            ]

        if scope != "created":

            llm_context["conversation"] = [
                self._turn_line(
                    position,
                    item,
                )
                for position, item in enumerate(
                    turns,
                    start=1,
                )
            ]

        return {
            "module": "conversation_recall",
            "llm_context": llm_context,
        }

    # ==================================================
    # HELPERS
    # ==================================================

    @staticmethod
    def _empty_answer(
        *,
        scope,
        actions,
        turns,
    ) -> str | None:

        if scope == "created":

            if not actions:

                return (
                    "As per my memory, I haven't created anything "
                    "in this conversation yet."
                )

            return None

        if scope == "asked":

            if not turns:

                return (
                    "As per my memory, you haven't asked me "
                    "anything in this conversation yet."
                )

            return None

        if not actions and not turns:

            return (
                "As per my memory, this is the start of our "
                "conversation and you haven't asked me anything yet."
            )

        return None

    @staticmethod
    def _action_line(
        position: int,
        record: dict,
    ) -> dict:

        status = record.get(
            "status"
        )

        return {
            "order": position,
            "what": record.get("description"),
            "status": STATUS_LABELS.get(
                status,
                status,
            ),
            "student_request": record.get("query"),
        }

    @staticmethod
    def _turn_line(
        position: int,
        turn,
    ) -> dict:

        answer = (
            turn.summary
            or ""
        ).strip()

        if len(answer) > MAX_ANSWER_CHARS:

            answer = (
                answer[:MAX_ANSWER_CHARS].rstrip()
                + "..."
            )

        return {
            "order": position,
            "student_asked": turn.query,
            "about": (
                turn.predicted_intent
                or ""
            ).replace("_", " "),
            "atlas_answered": answer,
        }

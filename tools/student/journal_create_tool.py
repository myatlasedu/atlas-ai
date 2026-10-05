from cache.pending_action_cache import (
    PendingActionCache
)

from services.chat_session_service import (
    current_turn
)

from services.journal_extractor import (
    JournalExtractor
)


class JournalCreateTool:

    async def run(
        self,
        context,
        parsed_intent
    ):
        # The journal creation feature is not yet implemented, so we return a placeholder response.
        return {
            "module": "journal",
            "direct_answer": "Journal update coming soon."
        }
    
        extractor = (
            JournalExtractor()
        )

        journal = await (
            extractor.extract(
                parsed_intent.original_query
            )
        )

        content = journal.get(
            "content",
            ""
        ).strip()

        if not content:

            message = (
                "I couldn't find any journal content to save. "
                "Please tell me what you'd like to add to your journal."
            )

            # No action is proposed, so this reply must reach the
            # student as-is: journal_create has no summarizer prompt.

            return {

                "module": "journal",

                "error": message,

                "direct_answer": message,
            }

        await PendingActionCache.save(

            user_id=context.user_id,

            action_type="create_journal",

            payload=journal,

            session_id=getattr(
                current_turn.get(),
                "session_id",
                None,
            ),
        )
        
        content = journal["content"].strip()

        preview = (

            content[:200]

            + "..."

            if len(content) > 200

            else content
        )

        return {

            "module":
                "journal",

            "action_required":
                True,

            "confirmation_required":
                True,

            "action_type":
                "create_journal",

            "payload":
                journal,

            "preview":
                preview,

            "llm_context": {

                "action":
                    "create_journal",

                "content":
                    content,
            },

            "confirmation_message":
                "Would you like me to save this journal entry?"
        }
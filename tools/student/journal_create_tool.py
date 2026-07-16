from cache.pending_action_cache import (
    PendingActionCache
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

            return {

                "module": "journal",

                "error":
                    "I couldn't find any journal content to save. Please tell me what you'd like to add to your journal."
            }

        await PendingActionCache.save(

            user_id=context.user_id,

            action_type="create_journal",

            payload=journal
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
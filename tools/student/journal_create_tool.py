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

        await PendingActionCache.save(

            user_id=context.user_id,

            action_type="create_journal",

            payload=journal
        )
        
        preview = (
            journal["content"][:200]
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

            "confirmation_message":
                (
                    "Would you like me to save "
                    "this journal entry?\n\n"
                    f"{preview}"
                )
        }
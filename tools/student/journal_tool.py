from db.session import (
    AsyncSessionLocal
)

from db.repositories.student.journal_repository import (
    JournalRepository
)


class JournalTool:

    async def run(
        self,
        context,
        parsed_intent,
    ):

        async with AsyncSessionLocal() as db:

            repo = JournalRepository(
                db
            )

            keyword = getattr(
                parsed_intent,
                "topic",
                None,
            )

            start_date = getattr(
                parsed_intent,
                "start_date",
                None,
            )

            end_date = getattr(
                parsed_intent,
                "end_date",
                None,
            )

            query = (
                getattr(
                    parsed_intent,
                    "original_query",
                    "",
                )
                .lower()
            )

            #
            # Latest journal
            #

            if any(
                phrase in query
                for phrase in [
                    "latest",
                    "last journal",
                    "recent journal",
                    "newest",
                ]
            ):

                latest = await repo.get_latest_entry(
                    context.user_id
                )

                if latest:

                    return {

                        "module": "journal",

                        "entry_count": 1,

                        "entries": [latest],

                        "llm_context": {

                            "entry_count": 1,

                            "latest_entry": latest,

                            "entries": [latest],
                        },

                        "direct_answer": (

                            f"Latest journal entry "
                            f"({latest['created_at'].strftime('%Y-%m-%d')}):\n\n"
                            f"{latest['content']}"
                        ),
                    }

                return {
                    "module": "journal",
                    "entry_count": 0,
                    "entries": [],
                    "direct_answer": (
                        "You do not have any journal entries yet."
                    ),
                }

            #
            # First journal
            #

            if any(
                phrase in query
                for phrase in [
                    "first journal",
                    "oldest journal",
                    "earliest journal",
                ]
            ):

                oldest = await repo.get_oldest_entry(
                    context.user_id
                )

                if oldest:

                    return {
                        "module": "journal",
                        "entry_count": 1,
                        "entries": [oldest],
                        "direct_answer": (
                            f"First journal entry "
                            f"({oldest['created_at'].strftime('%Y-%m-%d')}):\n\n"
                            f"{oldest['content']}"
                        ),

                        "llm_context": {

                            "entry_count": 1,

                            "latest_entry": oldest,

                            "entries": [oldest],
                        },
                    }

                return {
                    "module": "journal",
                    "entry_count": 0,
                    "entries": [],
                    "direct_answer": (
                        "You do not have any journal entries yet."
                    ),
                }

            #
            # General search
            #

            journals = await repo.search_entries(
                user_id=context.user_id,
                start_date=start_date,
                end_date=end_date,
                keyword=keyword,
            )

            payload = {

                "module": "journal",

                "entry_count": len(
                    journals
                ),

                "entries": journals,

                "llm_context": {

                    "entry_count": len(
                        journals
                    ),

                    "latest_entry": (

                        journals[0]

                        if journals

                        else None
                    ),

                    "entries": journals,
                }
            }

            if journals:

                lines = [

                    f"Found {len(journals)} journal entr{'y' if len(journals)==1 else 'ies'}.",
                    "",
                ]

                for entry in journals:

                    lines.append(

                        f"• [{entry['created_at']}] "
                        f"{entry['content'][:120]}"
                    )

                payload["direct_answer"] = "\n".join(
                    lines
                )

            else:

                if keyword:

                    payload["direct_answer"] = (
                        f"No journal entries were found matching '{keyword}'."
                    )

                elif start_date or end_date:

                    payload["direct_answer"] = (
                        "No journal entries were found in that date range."
                    )

                else:

                    payload["direct_answer"] = (
                        "You do not have any journal entries yet."
                    )

            return payload
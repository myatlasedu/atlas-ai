from db.session import (
    AsyncSessionLocal
)

from db.repositories.journal_repository import (
    JournalRepository
)


class JournalTool:

    async def run(
        self,
        context,
        parsed_intent
    ):

        async with AsyncSessionLocal() as db:

            repo = JournalRepository(
                db
            )

            journals = await (
                repo.get_recent_entries(
                    student_id=
                        context.student_id
                )
            )

            payload = {

                "module":
                    "journal",

                "entry_count":
                    len(journals),

                "entries":
                    journals
            }

        if journals:

            latest_entries = journals[:5]

            lines = [

                f"You have {len(journals)} journal entries.",
                "",
                "Recent entries:"
            ]

            for entry in latest_entries:

                created_at = (
                    entry["created_at"]
                    .strftime("%Y-%m-%d")
                )

                lines.append(
                    f"• [{created_at}] "
                    f"{entry['content'][:100]}"
                )

            payload["direct_answer"] = (
                "\n".join(lines)
            )

        else:

            payload["direct_answer"] = (
                "You do not have any journal entries yet."
            )

        return payload
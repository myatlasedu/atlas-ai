import calendar

from datetime import timedelta

from db.session import (
    AsyncSessionLocal
)

from db.repositories.student.journal_repository import (
    JournalRepository
)

from intents.student.enums import (
    StudentIntent
)

from utils import ist_today


PLANNER_TAGS = (
    "Academic",
    "Personal",
    "Task",
    "Note",
)

DEFAULT_PLANNER_TAG = "Note"


class PlannerTool:

    async def run(
        self,
        context,
        parsed_intent,
    ):

        async with AsyncSessionLocal() as db:

            repo = JournalRepository(
                db
            )

            if (
                parsed_intent.intent
                ==
                StudentIntent.PLANNER_CREATE
            ):

                return await self._create(
                    repo,
                    context,
                    parsed_intent,
                )

            return await self._summary(
                repo,
                context,
                parsed_intent,
            )

    async def _create(
        self,
        repo,
        context,
        parsed_intent,
    ):

        description = (
            parsed_intent.description
            or ""
        ).strip()

        if not description:

            return {
                "module": "planner",
                "direct_answer": (
                    "I couldn't find anything to add to your planner. "
                    "Please tell me what you'd like to plan."
                ),
            }

        tag = (
            parsed_intent.tag
            or ""
        ).strip().title()

        if tag not in PLANNER_TAGS:

            tag = DEFAULT_PLANNER_TAG

        planner_date = (
            parsed_intent.start_date
            or ist_today()
        )

        # A planner entry is a journal row with no subject offering;
        # create_entry leaves subject_offering_id NULL.

        planner_id = await repo.create_entry(
            user_id=context.user_id,
            content=description,
            tag=tag,
            journal_date=planner_date,
        )

        # create_entry returns None when the insert failed.

        if planner_id is None:

            return {
                "module": "planner",
                "direct_answer": (
                    "I couldn't save that to your planner. "
                    "Please try again."
                ),
            }

        return {
            "module": "planner",
            "direct_answer": (
                f"Added to your planner for "
                f"{planner_date.strftime('%d %b %Y')} "
                f"({tag}): {description}"
            ),
        }

    async def _summary(
        self,
        repo,
        context,
        parsed_intent,
    ):

        start_date = parsed_intent.start_date

        end_date = parsed_intent.end_date

        query = (
            parsed_intent.raw_query
            or parsed_intent.original_query
        ).lower()

        # Date resolution ends "this week" / "this month" at today,
        # but a planner also holds the days still to come.

        if start_date and "this week" in query:

            end_date = start_date + timedelta(
                days=6
            )

        elif start_date and "this month" in query:

            end_date = start_date.replace(
                day=calendar.monthrange(
                    start_date.year,
                    start_date.month,
                )[1]
            )

        entries = await repo.search_planner_entries(
            user_id=context.user_id,
            start_date=start_date,
            end_date=end_date,
            keyword=parsed_intent.topic,
        )

        if not entries:

            return {
                "module": "planner",
                "direct_answer": (
                    "No planner entries were found."
                ),
            }

        lines = [

            f"Found {len(entries)} planner entr{'y' if len(entries) == 1 else 'ies'}.",
            "",
        ]

        for entry in entries:

            lines.append(

                f"• [{entry['journal_date'].strftime('%d %b %Y')}] "
                f"({entry['tag']}) "
                f"{entry['content'][:120]}"
            )

        return {
            "module": "planner",
            "direct_answer": "\n".join(
                lines
            ),
        }

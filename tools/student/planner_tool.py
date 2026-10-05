import calendar
import re

from datetime import timedelta

from cache.pending_action_cache import (
    PendingActionCache
)

from db.session import (
    AsyncSessionLocal
)

from db.repositories.student.journal_repository import (
    JournalRepository
)

from intents.student.enums import (
    StudentIntent
)

from services.chat_session_service import (
    current_turn
)

from utils import ist_today


PLANNER_TAGS = (
    "Academic",
    "Personal",
    "Task",
    "Note",
)

DEFAULT_PLANNER_TAG = "Note"

RANKED_LIMIT = 5

LATEST_WORDS = {"latest", "recent", "newest", "last"}

OLDEST_WORDS = {"oldest", "first", "earliest"}

UPCOMING_WORDS = {"upcoming", "next", "coming", "future"}


def format_day(value) -> str:

    return value.strftime("%d %b %Y")


class PlannerTool:

    async def run(
        self,
        context,
        parsed_intent,
    ):

        if (
            parsed_intent.intent
            ==
            StudentIntent.PLANNER_CREATE
        ):

            return await self._propose(
                context,
                parsed_intent,
            )

        async with AsyncSessionLocal() as db:

            return await self._summary(
                JournalRepository(
                    db
                ),
                context,
                parsed_intent,
            )

    async def _propose(
        self,
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

        planner = {
            "content": description,
            "tag": tag,
            "journal_date": planner_date.isoformat(),
        }

        await PendingActionCache.save(

            user_id=context.user_id,

            action_type="create_planner",

            payload=planner,

            session_id=getattr(
                current_turn.get(),
                "session_id",
                None,
            ),
        )

        return {

            "module":
                "planner",

            "action_required":
                True,

            "confirmation_required":
                True,

            "action_type":
                "create_planner",

            "payload":
                planner,

            "confirmation_message": (
                f"Would you like me to add this to your planner "
                f"for {format_day(planner_date)} ({tag})?\n\n"
                f"{description}"
            ),
        }

    async def _summary(
        self,
        repo,
        context,
        parsed_intent,
    ):

        today = ist_today()

        start_date = parsed_intent.start_date

        end_date = parsed_intent.end_date

        query = (
            parsed_intent.raw_query
            or parsed_intent.original_query
        ).lower()

        words = set(
            re.findall(
                r"[a-z]+",
                query,
            )
        )

        has_range = bool(
            start_date
            or end_date
        )

        ascending = False

        limit = 20

        if not has_range and words & LATEST_WORDS:

            label = "latest planners"

            limit = RANKED_LIMIT

        elif not has_range and words & OLDEST_WORDS:

            label = "oldest planners"

            ascending = True

            limit = RANKED_LIMIT

        elif not has_range and words & UPCOMING_WORDS:

            label = "upcoming planners"

            start_date = today

            ascending = True

        elif not has_range:

            # No range asked for: the current week, Monday to Sunday.

            label = "current week planners"

            start_date = today - timedelta(
                days=today.weekday()
            )

            end_date = start_date + timedelta(
                days=6
            )

        else:

            if start_date and end_date == today and "week" in words:

                end_date = start_date + timedelta(
                    days=6
                )

            elif start_date and end_date == today and "month" in words:

                end_date = start_date.replace(
                    day=calendar.monthrange(
                        start_date.year,
                        start_date.month,
                    )[1]
                )

            if start_date and end_date and start_date != end_date:

                label = (
                    f"planners from {format_day(start_date)} "
                    f"to {format_day(end_date)}"
                )

            else:

                label = (
                    f"planners for "
                    f"{format_day(start_date or end_date)}"
                )

        entries = await repo.search_planner_entries(
            user_id=context.user_id,
            start_date=start_date,
            end_date=end_date,
            keyword=parsed_intent.topic,
            limit=limit,
            ascending=ascending,
        )

        if not entries:

            return {
                "module": "planner",
                "direct_answer": (
                    f"You have no {label}."
                ),
            }

        lines = [

            f"Your {label}:",
            "",
        ]

        for entry in entries:

            lines.append(

                f"• [{format_day(entry['journal_date'])}] "
                f"({entry['tag']}) "
                f"{entry['content'][:120]}"
            )

        return {
            "module": "planner",
            "direct_answer": "\n".join(
                lines
            ),
        }

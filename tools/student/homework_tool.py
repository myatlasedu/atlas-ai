from db.session import (
    AsyncSessionLocal
)

from db.repositories.student.homework_repository import (
    HomeworkRepository
)


class HomeworkTool:

    async def run(
        self,
        context,
        parsed_intent
    ):

        if not context.enrollment_id:

            return {

                "module":
                    "homework",

                "error":
                    "Enrollment ID missing",

                "direct_answer":
                    "Unable to load homework information."
            }

        async with AsyncSessionLocal() as db:

            repo = HomeworkRepository(
                db
            )

            pending = (
                await repo.get_pending_homework(
                    context.enrollment_id
                )
            )

            overdue = (
                await repo.get_overdue_homework(
                    context.enrollment_id
                )
            )

            due_today = (
                await repo.get_due_today(
                    context.enrollment_id
                )
            )

            due_tomorrow = (
                await repo.get_due_tomorrow(
                    context.enrollment_id
                )
            )

            feedback = (
                await repo.get_recent_feedback(
                    context.enrollment_id
                )
            )

            payload = {

                "module":
                    "homework",

                "pending_count":
                    len(pending),

                "overdue_count":
                    len(overdue),

                "pending":
                    pending,

                "overdue":
                    overdue,

                "due_today":
                    due_today,

                "due_tomorrow":
                    due_tomorrow,

                "recent_feedback":
                    feedback
            }

        # =====================================
        # DIRECT ANSWER
        # =====================================

        lines = []

        if pending:

            lines.append(
                f"You have {len(pending)} pending homework assignment(s)."
            )

        if overdue:

            lines.append(
                f"{len(overdue)} homework assignment(s) are overdue."
            )

        if due_today:

            lines.append(
                f"{len(due_today)} homework assignment(s) are due today."
            )

        if due_tomorrow:

            lines.append(
                f"{len(due_tomorrow)} homework assignment(s) are due tomorrow."
            )

        if feedback:

            lines.append(
                f"You have feedback on {len(feedback)} homework assignment(s)."
            )

        if pending:

            lines.append("")
            lines.append("Pending homework:")

            for item in pending[:5]:

                lines.append(
                    f"• {item['title']}"
                )

        if overdue:

            lines.append("")
            lines.append("Overdue homework:")

            for item in overdue[:5]:

                lines.append(
                    f"• {item['title']}"
                )

        if not lines:

            payload["direct_answer"] = (
                "You currently have no pending homework."
            )

        else:

            payload["direct_answer"] = (
                "\n".join(lines)
            )

        return payload
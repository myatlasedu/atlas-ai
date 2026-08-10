from db.session import (
    AsyncSessionLocal,
)

from db.repositories.student.homework_repository import (
    HomeworkRepository,
)

from llm.builders.homework_builder import (
    build_homework_llm_context,
)


class HomeworkTool:

    async def run(
        self,
        context,
        parsed_intent,
    ):

        if not context.enrollment_id:

            return {

                "module":
                    "homework",

                "error":
                    "Enrollment ID missing",

                "direct_answer":
                    "Unable to load homework information.",
            }

        # =====================================
        # SPECIFIC HOMEWORK MARKS LOOKUP
        # Only when the query asks for marks /
        # grade on a specific titled homework.
        # =====================================

        title = getattr(
            parsed_intent,
            "topic",
            None,
        )

        if title:

            title = (
                str(title)
                .strip()
            )

        asks_for_marks = getattr(
            parsed_intent,
            "asks_for_marks",
            False,
        )

        if (
            title
            and
            asks_for_marks
        ):

            async with AsyncSessionLocal() as db:

                repo = HomeworkRepository(
                    db
                )

                marks = (
                    await repo.get_homework_mark_state(
                        context.enrollment_id,
                        title,
                    )
                )

            if marks.get("state") == "marks":

                marks_obtained = int(
                    round(
                        float(
                            marks["marks_obtained"]
                        )
                    )
                )

                total_marks = int(
                    round(
                        float(
                            marks["total_marks"]
                        )
                    )
                )

                percentage = int(
                    round(
                        float(
                            marks["percentage"]
                        )
                    )
                )

                return {
                    "module": "homework",
                    "title": marks["title"],
                    "marks_obtained": marks_obtained,
                    "total_marks": total_marks,
                    "percentage": percentage,
                    "reviewed_at": marks["reviewed_at"],
                    "attempt_number": marks["attempt_number"],
                    "direct_answer": (
                        f"Your mark for {marks['title']} "
                        f"is {marks_obtained}/{total_marks} "
                        f"({percentage}%)."
                    ),
                    "llm_context": build_homework_llm_context({
                        "titled_mark": {
                            "title": marks["title"],
                            "marks_obtained": marks_obtained,
                            "total_marks": total_marks,
                            "percentage": percentage,
                            "attempt_number": marks["attempt_number"],
                        },
                        "pending": [],
                        "overdue": [],
                        "due_today": [],
                        "due_tomorrow": [],
                        "recent_feedback": [],
                    }),
                }

            if marks.get("state") in (
                "assigned_not_submitted",
                "not_assigned",
                "not_found",
            ):

                return {
                    "module": "homework",
                    "title": marks.get("title", title),
                    "direct_answer": "",
                    "llm_context": build_homework_llm_context({
                        "titled_mark": None,
                        "titled_lookup": {
                            "state": marks.get("state"),
                            "title": marks.get("title", title),
                        },
                        "pending": [],
                        "overdue": [],
                        "due_today": [],
                        "due_tomorrow": [],
                        "recent_feedback": [],
                    }),
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
                    feedback,
            }

        # =====================================
        # LLM CONTEXT
        # =====================================

        payload["llm_context"] = (
            build_homework_llm_context(
                payload
            )
        )

        # =====================================
        # DIRECT ANSWER (Temporary)
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
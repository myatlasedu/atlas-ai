from datetime import date
from datetime import timedelta

import difflib

from db.session import (
    AsyncSessionLocal,
)

from db.repositories.student.homework_repository import (
    HomeworkRepository,
)

from llm.builders.homework_builder import (
    build_homework_llm_context,
)

from utils import (
    ist_today,
)


def coerce_date(value):

    if isinstance(
        value,
        date,
    ):

        return value

    try:

        return date.fromisoformat(
            str(value)[:10]
        )

    except (TypeError, ValueError):

        return None


def empty_payload(
    focus,
):

    return {
        "module": "homework",
        "focus": focus,
        "pending_count": 0,
        "overdue_count": 0,
        "submitted_count": 0,
        "graded_count": 0,
        "pending": [],
        "overdue": [],
        "due_today": [],
        "due_tomorrow": [],
        "recent_feedback": [],
        "submitted": [],
        "graded": [],
        "next_up": None,
    }


class HomeworkTool:

    async def resolve_title_reply(
        self,
        repo,
        enrollment_id,
        title,
        asks_for_marks,
    ):

        #
        # Runs whenever a SPECIFIC homework is named.
        # The repository decides the true state from the
        # latest attempt only, so every reply below is a
        # database fact, never an invention.
        #

        marks = (
            await repo.get_homework_mark_state(
                enrollment_id,
                title,
            )
        )

        #
        # Typo safety net: when the exact title misses,
        # compare the student's words against the real
        # homework titles deterministically (letter
        # similarity, never an AI guess). A strong match
        # is answered transparently; a miss falls through
        # to an honest acknowledgment.
        #

        close_match_note = ""

        if marks.get("state") == "not_found":

            candidates = marks.get("candidates") or []

            close_match = difflib.get_close_matches(
                title.lower(),
                [
                    candidate.lower()
                    for candidate in candidates
                ],
                n=1,
                cutoff=0.85,
            ) if candidates else []

            if close_match:

                canonical = next(
                    candidate
                    for candidate in candidates
                    if candidate.lower() == close_match[0]
                )

                retry = await repo.get_homework_mark_state(
                    enrollment_id,
                    canonical,
                )

                if retry.get("state") != "not_found":

                    marks = retry

                    close_match_note = (
                        f"Showing closest match '{canonical}'. "
                    )

        state = marks.get("state")

        if state == "not_found":

            return await self.build_not_found_overview_reply(
                repo,
                enrollment_id,
                title,
            )

        if state == "marks":

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

            titled_mark = {
                "title": marks["title"],
                "subject": marks.get("subject_name"),
                "teacher": marks.get("teacher_name"),
                "due_date": str(marks["due_date"])[:10] if marks.get("due_date") else None,
                "submitted_at": str(marks["submitted_at"])[:16] if marks.get("submitted_at") else None,
                "reviewed_at": str(marks["reviewed_at"])[:16] if marks.get("reviewed_at") else None,
                "marks_obtained": marks_obtained,
                "total_marks": total_marks,
                "percentage": percentage,
                "attempt_number": marks.get("attempt_number"),
            }

            direct = (
                f"{close_match_note}"
                f"Your mark for {marks['title']} "
                f"is {marks_obtained}/{total_marks} "
                f"({percentage}%)."
            )

            return {
                "module": "homework",
                "focus": "topic_status",
                "title": marks["title"],
                "titled_mark": titled_mark,
                "direct_answer": direct,
                "llm_context": build_homework_llm_context({
                    "focus": "topic_status",
                    "titled_mark": titled_mark,
                }),
            }

        reply_by_state = {
            "submitted_not_graded":
                "has been submitted and is awaiting review.",
            "resubmit_requested":
                "was sent back by the teacher for a redo.",
            "assigned_not_submitted":
                "is assigned to you but not submitted yet.",
            "not_assigned":
                "could not be found in your records.",
            "not_found":
                "could not be found with that exact title.",
        }

        message = reply_by_state.get(
            state,
            reply_by_state["not_found"],
        )

        #
        # Duplicate titles: several real homework rows can
        # share one title. Count them explicitly instead of
        # narrating just the first row.
        #

        duplicate_note = ""

        matches = marks.get("matches") or []

        if len(matches) > 1:

            duplicate_count = len(matches)

            due_dates = sorted({
                match["due_date"]
                for match in matches
                if match["due_date"]
            })

            not_submitted = sum(
                1
                for match in matches
                if not match["submitted"]
            )

            graded_total = sum(
                1
                for match in matches
                if match["graded"]
            )

            duplicate_note = (
                f"You have {duplicate_count} assignments "
                f"titled '{marks.get('title', title)}'"
            )

            if due_dates:

                duplicate_note += (
                    f" (due {', '.join(due_dates)})"
                )

            status_bits = []

            if graded_total:

                status_bits.append(
                    f"{graded_total} graded"
                )

            if not_submitted:

                status_bits.append(
                    f"{not_submitted} not submitted yet"
                )

            if status_bits:

                duplicate_note += (
                    " - " + ", ".join(status_bits) + "."
                )

            else:

                duplicate_note += "."

        titled_lookup = {
            "state": state,
            "title": marks.get("title", title),
            "subject": marks.get("subject_name"),
            "teacher": marks.get("teacher_name"),
            "due_date": str(marks["due_date"])[:10] if marks.get("due_date") else None,
            "submitted_at": str(marks["submitted_at"])[:16] if marks.get("submitted_at") else None,
        }

        if close_match_note:

            titled_lookup["note"] = (
                close_match_note.strip()
            )

        if duplicate_note:

            titled_lookup["duplicate_note"] = (
                duplicate_note
            )

        return {
            "module": "homework",
            "focus": "topic_status",
            "title": marks.get("title", title),
            "titled_mark": None,
            "titled_lookup": titled_lookup,
            "direct_answer": (
                f"{close_match_note}{duplicate_note}"
            ),
            "llm_context": build_homework_llm_context({
                "focus": "topic_status",
                "titled_lookup": titled_lookup,
            }),
        }

    async def build_not_found_overview_reply(
        self,
        repo,
        enrollment_id,
        title,
    ):

        #
        # Honest dead end: the title matched nothing, not
        # even a close spelling. Acknowledge the miss in
        # plain words first, THEN hand over the general
        # homework status instead of pretending the
        # question was never asked.
        #

        overview_rows = await repo.get_pending_homework(
            enrollment_id,
            include_submitted=True,
        )

        payload = empty_payload("general")

        payload["overdue"] = [
            row for row in overview_rows
            if row["status_tag"] == "overdue"
        ]

        payload["pending"] = [
            row for row in overview_rows
            if row["status_tag"] == "pending"
        ]

        payload["submitted"] = [
            row for row in overview_rows
            if row["status_tag"] == "submitted"
        ]

        payload["graded"] = [
            row for row in overview_rows
            if row["status_tag"] == "graded"
        ]

        payload["pending_count"] = (
            len(payload["pending"])
            + len(payload["overdue"])
        )

        payload["overdue_count"] = len(payload["overdue"])

        payload["submitted_count"] = len(payload["submitted"])

        payload["graded_count"] = len(payload["graded"])

        ack_line = (
            f"I couldn't find any homework titled "
            f"'{title}' - please check the spelling. "
            f"Here is your homework status instead:"
        )

        llm_context = build_homework_llm_context(payload)

        llm_context["headline"] = (
            f"No homework titled '{title}' was found."
        )

        llm_context["titled_lookup"] = {
            "state": "not_found",
            "title": title,
        }

        return {
            "module": "homework",
            "focus": "topic_status",
            "title": title,
            "titled_mark": None,
            "titled_lookup": llm_context["titled_lookup"],
            "direct_answer": (
                f"{ack_line}\n\n"
                + self.build_direct_answer(
                    "general",
                    payload,
                )
            ),
            "llm_context": llm_context,
        }

    def format_item_line(
        self,
        item,
    ):

        title = item.get(
            "title",
            "Homework",
        )

        parts = [title]

        if item.get("status_tag") == "overdue" or item.get("is_overdue"):

            parts.append("(overdue)")

        return "• " + " ".join(parts)

    async def run(
        self,
        context,
        parsed_intent,
    ):

        if not context.enrollment_id:

            return {
                "module": "homework",
                "error": "Enrollment ID missing",
                "direct_answer": "Unable to load homework information.",
            }

        title = getattr(
            parsed_intent,
            "topic",
            None,
        )

        if title:

            title = str(title).strip()

        focus = getattr(
            parsed_intent,
            "homework_focus",
            None,
        ) or (
            "topic_status"
            if title
            else "general"
        )

        asks_for_marks = getattr(
            parsed_intent,
            "asks_for_marks",
            False,
        )

        subject = getattr(
            parsed_intent,
            "subject",
            None,
        )

        enrollment_id = context.enrollment_id

        # =====================================
        # TITLED LOOKUP - always runs when a
        # specific homework is named.
        # =====================================

        if title:

            async with AsyncSessionLocal() as db:

                repo = HomeworkRepository(
                    db
                )

                return await self.resolve_title_reply(
                    repo,
                    enrollment_id,
                    title,
                    asks_for_marks,
                )

        payload = empty_payload(focus)

        today = ist_today()

        async with AsyncSessionLocal() as db:

            repo = HomeworkRepository(
                db
            )

            # =====================================
            # PENDING
            # =====================================

            if focus == "pending":

                rows = await repo.get_pending_homework(
                    enrollment_id,
                    subject=subject,
                )

                payload["pending"] = rows

            # =====================================
            # OVERDUE
            # =====================================

            elif focus == "overdue":

                rows = await repo.get_overdue_homework(
                    enrollment_id,
                    subject=subject,
                )

                payload["overdue"] = rows

            # =====================================
            # DUE TODAY / TOMORROW
            # =====================================

            elif focus == "due_today":

                rows = await repo.get_due_today(
                    enrollment_id
                )

                payload["due_today"] = rows

            elif focus == "due_tomorrow":

                rows = await repo.get_due_tomorrow(
                    enrollment_id
                )

                payload["due_tomorrow"] = rows

            # =====================================
            # SUBMITTED / GRADED
            # One wide query, sliced in Python.
            # =====================================

            elif focus in (
                "submitted",
                "graded",
            ):

                rows = await repo.get_pending_homework(
                    enrollment_id,
                    subject=subject,
                    include_submitted=True,
                )

                if focus == "submitted":

                    on = (
                        coerce_date(
                            getattr(parsed_intent, "start_date", None)
                        )
                        or coerce_date(
                            getattr(parsed_intent, "end_date", None)
                        )
                    )

                    if on:

                        rows = [
                            r for r in rows
                            if r["status_tag"] in ("submitted", "graded")
                            and r.get("submitted_at")
                            and r["submitted_at"].date() == on
                        ]

                    else:

                        rows = [
                            r for r in rows
                            if r["status_tag"] in ("submitted", "graded")
                        ]

                    payload["submitted"] = rows

                else:

                    payload["graded"] = [
                        r for r in rows
                        if r["status_tag"] == "graded"
                    ]

            # =====================================
            # FEEDBACK
            # =====================================

            elif focus == "feedback":

                payload["recent_feedback"] = (
                    await repo.get_recent_feedback(
                        enrollment_id
                    )
                )

            # =====================================
            # DUE RANGE (this week / any window)
            # =====================================

            elif focus == "due_range":

                start = coerce_date(
                    getattr(parsed_intent, "start_date", None)
                )

                end = coerce_date(
                    getattr(parsed_intent, "end_date", None)
                )

                if not (start and end):

                    monday = today - timedelta(
                        days=today.weekday()
                    )

                    start = monday

                    end = monday + timedelta(days=6)

                rows = await repo.get_pending_homework(
                    enrollment_id,
                    subject=subject,
                    start=start,
                    end=end,
                    include_submitted=True,
                )

                payload["due_window"] = {
                    "start": start.isoformat(),
                    "end": end.isoformat(),
                }

                payload["pending"] = [
                    r for r in rows
                    if r["status_tag"] == "pending"
                ]

                payload["overdue"] = [
                    r for r in rows
                    if r["status_tag"] == "overdue"
                ]

                payload["submitted"] = [
                    r for r in rows
                    if r["status_tag"] in ("submitted", "graded")
                ]

            # =====================================
            # NEXT UP
            # =====================================

            elif focus == "next_up":

                rows = await repo.get_pending_homework(
                    enrollment_id,
                    subject=subject,
                )

                nxt = next(
                    (
                        r for r in rows
                        if not r["is_overdue"]
                    ),
                    None,
                )

                payload["next_up"] = nxt

            # =====================================
            # GENERAL - one wide query, deduped
            # sections built in Python.
            # =====================================

            else:

                rows = await repo.get_pending_homework(
                    enrollment_id,
                    subject=subject,
                    include_submitted=True,
                )

                payload["overdue"] = [
                    r for r in rows
                    if r["status_tag"] == "overdue"
                ]

                payload["pending"] = [
                    r for r in rows
                    if r["status_tag"] == "pending"
                ]

                payload["submitted"] = [
                    r for r in rows
                    if r["status_tag"] == "submitted"
                ]

                payload["graded"] = [
                    r for r in rows
                    if r["status_tag"] == "graded"
                ]

        payload["pending_count"] = (
            len(payload["pending"])
            + len(payload["overdue"])
        )

        payload["overdue_count"] = (
            len(payload["overdue"])
        )

        payload["submitted_count"] = (
            len(payload["submitted"])
        )

        payload["graded_count"] = (
            len(payload["graded"])
        )

        payload["due_today_count"] = (
            len(payload["due_today"])
        )

        payload["due_tomorrow_count"] = (
            len(payload["due_tomorrow"])
        )

        payload["recent_feedback_count"] = (
            len(payload["recent_feedback"])
        )

        # =====================================
        # LLM CONTEXT
        # =====================================

        payload["llm_context"] = (
            build_homework_llm_context(
                payload
            )
        )

        # =====================================
        # DIRECT ANSWER
        # =====================================

        payload["direct_answer"] = (
            self.build_direct_answer(
                focus,
                payload,
            )
        )

        return payload

    def build_direct_answer(
        self,
        focus,
        payload,
    ):

        lines = []

        pending = payload["pending"]

        overdue = payload["overdue"]

        if focus == "pending":

            if pending:

                lines.append(
                    f"You have {len(pending)} pending "
                    f"homework assignment(s)."
                )

                for item in pending[:10]:

                    lines.append(
                        self.format_item_line(item)
                    )

                extra = pending[10:]

                if extra:

                    lines.append(
                        f"...and {len(extra)} more."
                    )

            else:

                lines.append(
                    "You have no pending homework right now."
                )

        elif focus == "overdue":

            if overdue:

                lines.append(
                    f"{len(overdue)} homework assignment(s) "
                    f"are overdue:"
                )

                for item in overdue[:10]:

                    lines.append(
                        self.format_item_line(item)
                    )

                extra = overdue[10:]

                if extra:

                    lines.append(
                        f"...and {len(extra)} more."
                    )

            else:

                lines.append(
                    "Good news - you have nothing overdue."
                )

        elif focus == "due_today":

            rows = payload["due_today"]

            if rows:

                lines.append(
                    f"{len(rows)} homework assignment(s) "
                    f"are due today:"
                )

                for item in rows:

                    lines.append(
                        self.format_item_line(item)
                    )

            else:

                lines.append(
                    "You have no homework due today."
                )

        elif focus == "due_tomorrow":

            rows = payload["due_tomorrow"]

            if rows:

                lines.append(
                    f"{len(rows)} homework assignment(s) "
                    f"are due tomorrow:"
                )

                for item in rows:

                    lines.append(
                        self.format_item_line(item)
                    )

            else:

                lines.append(
                    "You have no homework due tomorrow."
                )

        elif focus == "submitted":

            rows = payload["submitted"]

            if rows:

                lines.append(
                    f"You have handed in "
                    f"{len(rows)} homework assignment(s):"
                )

                for item in rows[:10]:

                    stamp = (
                        str(item["submitted_at"])[:16]
                        if item.get("submitted_at")
                        else "date not recorded"
                    )

                    lines.append(
                        f"• {item['title']} - submitted {stamp}"
                    )

            else:

                lines.append(
                    "You haven't submitted any homework "
                    "matching that yet."
                )

        elif focus == "graded":

            rows = payload["graded"]

            if rows:

                lines.append(
                    f"{len(rows)} homework assignment(s) "
                    f"have been graded:"
                )

                for item in rows[:10]:

                    if item.get("marks_obtained") is not None:

                        pct = int(round(
                            float(item["marks_obtained"])
                            / float(item["total_marks"])
                            * 100
                        )) if item.get("total_marks") else 0

                        lines.append(
                            f"• {item['title']} - "
                            f"{int(round(float(item['marks_obtained'])))}"
                            f"/{int(round(float(item['total_marks'] or 0)))}"
                            f" ({pct}%)"
                        )

                    else:

                        lines.append(
                            f"• {item['title']}"
                        )

            else:

                lines.append(
                    "No graded homework found in your records yet."
                )

        elif focus == "feedback":

            rows = payload["recent_feedback"]

            if rows:

                lines.append(
                    f"Teacher feedback on {len(rows)} "
                    f"assignment(s):"
                )

                for item in rows:

                    note = (
                        item.get("teacher_note") or ""
                    ).strip()

                    lines.append(
                        f"• {item['title']} - {note}"
                    )

            else:

                lines.append(
                    "Your teachers haven't left any homework "
                    "feedback yet."
                )

        elif focus == "due_range":

            window = payload.get("due_window") or {}

            listed = pending + overdue

            if listed:

                lines.append(
                    f"Between {window.get('start')} and "
                    f"{window.get('end')} there are "
                    f"{len(listed)} unfinished assignment(s)"
                    + (
                        f" and {payload['submitted_count']} handed in."
                        if payload["submitted"]
                        else "."
                    )
                )

                for item in listed[:15]:

                    lines.append(
                        self.format_item_line(item)
                    )

            else:

                lines.append(
                    f"No homework was due between "
                    f"{window.get('start')} and "
                    f"{window.get('end')}."
                )

        elif focus == "next_up":

            nxt = payload["next_up"]

            if nxt:

                lines.append(
                    f"{nxt['title']} comes first - "
                    f"due {str(nxt['due_date'])[:10]}."
                )

            else:

                lines.append(
                    "Nothing is coming due - you're all caught up."
                )

        else:

            # GENERAL

            total_open = (
                payload["pending_count"]
            )

            if total_open:

                lines.append(
                    f"You have {total_open} open assignment(s): "
                    f"{len(overdue)} overdue, "
                    f"{len(pending)} still upcoming."
                )

                if overdue:

                    lines.append("")
                    lines.append("Overdue:")

                    for item in overdue[:5]:

                        lines.append(
                            self.format_item_line(item)
                        )

                if pending:

                    lines.append("")
                    lines.append("Upcoming:")

                    for item in pending[:5]:

                        lines.append(
                            self.format_item_line(item)
                        )

                extra_note = []

                if payload["submitted_count"]:

                    extra_note.append(
                        f"{payload['submitted_count']} handed in"
                    )

                if payload["graded_count"]:

                    extra_note.append(
                        f"{payload['graded_count']} graded"
                    )

                if extra_note:

                    lines.append("")
                    lines.append(
                        "Also: " + ", ".join(extra_note) + "."
                    )

            else:

                lines.append(
                    "You currently have no pending homework."
                )

                if payload["graded_count"]:

                    lines.append(
                        f"{payload['graded_count']} graded "
                        f"assignment(s) on record."
                    )

        return "\n".join(lines)

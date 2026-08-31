from datetime import date
from datetime import timedelta

from db.session import (
    AsyncSessionLocal,
)

from db.repositories.student.homework_repository import (
    HomeworkRepository,
    RELATIVE_HOMEWORK_TITLES,
)

from llm.builders.homework_builder import (
    build_homework_llm_context,
)

from utils import (
    ist_today,
    format_datetime,
    IST,
    MARKS_QUERY_KEYWORDS,
    MARKS_MANIPULATION_KEYWORDS,
    resolve_canonical_name,
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
        "resubmit_count": 0,
        "upcoming_count": 0,
        "awaiting_marks_count": 0,
        "submitted_count": 0,
        "graded_count": 0,
        "pending": [],
        "overdue": [],
        "due_today": [],
        "due_tomorrow": [],
        "recent_feedback": [],
        "submitted": [],
        "graded": [],
        "resubmit": [],
        "upcoming": [],
        "awaiting_marks": [],
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

        # Runs when a specific homework is named; state comes from the latest attempt only.

        # Relative titles skip difflib (search all homework by date);
        # others match the full list via difflib (typo-tolerant).

        normalized_title = repo.normalize_title(title)

        is_relative = normalized_title in RELATIVE_HOMEWORK_TITLES

        close_match_note = ""

        if not is_relative:

            all_titles = await repo.list_enrollment_homework_titles(
                enrollment_id,
            )

            title_list = [
                t["title"]
                for t in all_titles
            ]

            canonical = resolve_canonical_name(
                title,
                title_list,
                cutoff=0.85,
            )

            if canonical:

                close_match_note = (
                    f"Showing closest match '{canonical}'. "
                )

            else:

                # Retry the title with filler words ("homework", "chapter", ...) stripped on both sides.
                def strip_filler(value):
                    normalized = value.strip().lower()
                    changed = True
                    while changed:
                        changed = False
                        for word in (
                            "homework",
                            "assignment",
                            "home work",
                            "chapter",
                            "work",
                        ):
                            if normalized.endswith(" " + word):
                                normalized = (
                                    normalized[: -len(word) - 1].strip()
                                )
                                changed = True
                    return normalized

                stripped_title = strip_filler(title)

                if stripped_title:

                    stripped_candidates = [
                        strip_filler(t)
                        for t in title_list
                    ]

                    match = resolve_canonical_name(
                        stripped_title,
                        stripped_candidates,
                        cutoff=0.85,
                    )

                    if match and match in stripped_candidates:

                        canonical = title_list[
                            stripped_candidates.index(match)
                        ]

                        close_match_note = (
                            f"Showing closest match '{canonical}'. "
                        )

                if not canonical:

                    if asks_for_marks:

                        candidate = None

                        lower_title = title.strip().lower()

                        for suffix in (
                            " homework",
                            " assignment",
                            " hw",
                            " work",
                        ):

                            if lower_title.endswith(suffix):

                                candidate = (
                                    lower_title[: -len(suffix)].strip()
                                )

                                break

                        if candidate:

                            graded_rows = (
                                await repo.get_pending_homework(
                                    enrollment_id,
                                    include_submitted=True,
                                )
                            )

                            matched = [
                                r for r in graded_rows
                                if r["status_tag"] == "graded"
                                and r.get("subject_name")
                                and candidate
                                in r["subject_name"].lower()
                            ]

                            if matched:

                                payload = empty_payload("graded")

                                payload["graded"] = matched

                                payload["graded_count"] = (
                                    len(matched)
                                )

                                return {
                                    "module": "homework",
                                    "focus": "graded",
                                    "graded": matched,
                                    "direct_answer": (
                                        self.build_direct_answer(
                                            "graded",
                                            payload,
                                        )
                                    ),
                                    "llm_context": (
                                        build_homework_llm_context(
                                            payload
                                        )
                                    ),
                                }

                    return await self.build_not_found_overview_reply(
                        repo,
                        enrollment_id,
                        title,
                    )

        else:

            canonical = title

        marks = await repo.get_homework_mark_state(
            enrollment_id,
            canonical,
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
                "teacher_note": marks.get("teacher_note"),
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

        # Duplicate titles: several rows can share one title; count them explicitly.

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
            "teacher_note": marks.get("teacher_note"),
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

        # Honest dead end: title matched nothing. Acknowledge the miss, then give the general status.

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

        payload["resubmit"] = [
            row for row in overview_rows
            if row["status_tag"] == "resubmit_requested"
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
            + len(payload["resubmit"])
        )

        payload["overdue_count"] = len(payload["overdue"])

        payload["resubmit_count"] = len(payload["resubmit"])

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

        if item.get("status_tag") == "resubmit_requested":

            parts.append("(resubmit)")

        elif item.get("status_tag") == "overdue":

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

        teacher = getattr(
            parsed_intent,
            "teacher",
            None,
        )

        late_only = getattr(
            parsed_intent,
            "late_only",
            False,
        )

        enrollment_id = context.enrollment_id

        query_lower = (
            getattr(parsed_intent, "original_query", "")
            or ""
        ).lower()

        if getattr(parsed_intent, "invalid_date", False):

            return {
                "module": "homework",
                "focus": focus,
                "direct_answer": (
                    "That date isn't valid - please check it "
                    "and try again."
                ),
            }

        if any(
            keyword in query_lower
            for keyword in MARKS_MANIPULATION_KEYWORDS
        ):

            return {
                "module": "homework",
                "focus": focus,
                "direct_answer": (
                    "I can't change or set your homework marks - "
                    "only a teacher can grade your work."
                ),
            }

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

        payload["subject"] = subject

        query_lower = (
            getattr(parsed_intent, "original_query", "")
            or ""
        ).lower()

        asked_marks = any(
            keyword in query_lower
            for keyword in MARKS_QUERY_KEYWORDS
        )

        if (
            asked_marks
            and not title
            and focus in ("pending", "overdue")
        ):

            owner = (
                "Your child's"
                if getattr(context, "role", None) == "guardian"
                else "Your"
            )

            return {
                "module": "homework",
                "focus": focus,
                "direct_answer": (
                    f"{owner} {focus} homework hasn't been graded "
                    f"yet, so there are no marks to show."
                ),
            }

        # Teacher / subject name resolution - reuses the rows the
        # existing homework query already returns (no new queries).
        teacher_candidate = None

        if not teacher:

            original_query = (
                getattr(parsed_intent, "original_query", "")
                or ""
            )

            for marker in (
                "'s homework",
                "'s assignment",
                "'s work",
            ):

                idx = query_lower.find(marker)

                if idx != -1:

                    teacher_candidate = (
                        original_query[:idx]
                        .rsplit(" ", 1)[-1]
                        .rstrip("'")
                    )

                    break

        if teacher or subject or teacher_candidate:

            async with AsyncSessionLocal() as db:

                repo = HomeworkRepository(
                    db
                )

                rows = await repo.get_pending_homework(
                    enrollment_id,
                    include_submitted=True,
                )

                if teacher or teacher_candidate:

                    names = sorted({
                        r["teacher_name"]
                        for r in rows
                        if r.get("teacher_name")
                    })

                    if teacher:

                        canonical = resolve_canonical_name(
                            teacher,
                            names,
                        )

                        if canonical:

                            teacher = canonical

                        else:

                            return {
                                "module": "homework",
                                "focus": focus,
                                "direct_answer": (
                                    f"No homework found from "
                                    f"teacher '{teacher}'."
                                ),
                            }

                    else:

                        canonical = resolve_canonical_name(
                            teacher_candidate,
                            names,
                        )

                        if canonical:

                            teacher = canonical

                if subject:

                    names = sorted({
                        r["subject_name"]
                        for r in rows
                        if r.get("subject_name")
                    })

                    canonical = resolve_canonical_name(
                        subject,
                        names,
                    )

                    if canonical:

                        subject = canonical

                    else:

                        titles = sorted({
                            r["title"]
                            for r in rows
                            if r.get("title")
                        })

                        canonical_title = resolve_canonical_name(
                            subject,
                            titles,
                        )

                        if canonical_title:

                            return await self.resolve_title_reply(
                                repo,
                                enrollment_id,
                                canonical_title,
                                False,
                            )

        payload["count_only"] = (
            "how many" in query_lower
            or "number of" in query_lower
        )

        payload["conversational"] = (
            "how is" in query_lower
            and "going" in query_lower
        )

        start = coerce_date(
            getattr(parsed_intent, "start_date", None)
        )

        end = coerce_date(
            getattr(parsed_intent, "end_date", None)
        )

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
                    teacher=teacher,
                    start=start,
                    end=end,
                )

                payload["pending"] = rows

            # =====================================
            # OVERDUE
            # =====================================

            elif focus == "overdue":

                rows = await repo.get_overdue_homework(
                    enrollment_id,
                    subject=subject,
                    teacher=teacher,
                    start=start,
                    end=end,
                )

                payload["overdue"] = rows

            # =====================================
            # DUE TODAY / TOMORROW
            # =====================================

            elif focus == "due_today":

                rows = await repo.get_due_today(
                    enrollment_id,
                    subject=subject,
                    teacher=teacher,
                )

                payload["due_today"] = rows

            elif focus == "due_tomorrow":

                rows = await repo.get_due_tomorrow(
                    enrollment_id,
                    subject=subject,
                    teacher=teacher,
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
                    teacher=teacher,
                    include_submitted=True,
                )

                if focus == "submitted":

                    if subject:

                        if (
                            rows
                            and rows[0].get("subject_name")
                        ):

                            payload["subject"] = (
                                rows[0]["subject_name"]
                            )

                        payload["pending"] = [
                            r for r in rows
                            if r["status_tag"] == "pending"
                        ]

                        payload["overdue"] = [
                            r for r in rows
                            if r["status_tag"] == "overdue"
                        ]

                        payload["resubmit"] = [
                            r for r in rows
                            if r["status_tag"] == "resubmit_requested"
                        ]

                    if start or end:

                        low = start or end

                        high = end or start

                        rows = [
                            r for r in rows
                            if r["status_tag"] in ("submitted", "graded")
                            and r.get("submitted_at")
                            and low <= r["submitted_at"].astimezone(IST).date() <= high
                        ]

                    else:

                        rows = [
                            r for r in rows
                            if r["status_tag"] in ("submitted", "graded")
                        ]

                    if late_only:

                        rows = [
                            r for r in rows
                            if r.get("submitted_at")
                            and r.get("due_date")
                            and (
                                r["submitted_at"].astimezone(IST).date()
                                > r["due_date"].date()
                            )
                        ]

                    payload["submitted"] = rows

                else:

                    graded = [
                        r for r in rows
                        if r["status_tag"] == "graded"
                    ]

                    if start or end:

                        low = start or date.min

                        high = end or date.max

                        graded = [
                            r for r in graded
                            if r.get("due_date")
                            and low <= r["due_date"].date() <= high
                        ]

                    payload["graded"] = graded

            # =====================================
            # FEEDBACK
            # =====================================

            elif focus == "feedback":

                payload["recent_feedback"] = (
                    await repo.get_recent_feedback(
                        enrollment_id,
                        subject=subject,
                    )
                )

            # =====================================
            # RESUBMIT
            # =====================================

            elif focus == "resubmit":

                rows = await repo.get_pending_homework(
                    enrollment_id,
                    subject=subject,
                    teacher=teacher,
                    start=start,
                    end=end,
                    include_submitted=True,
                )

                payload["resubmit"] = [
                    r for r in rows
                    if r["status_tag"] == "resubmit_requested"
                ]

            # =====================================
            # AWAITING MARKS (submitted, not graded)
            # =====================================

            elif focus == "awaiting_marks":

                rows = await repo.get_pending_homework(
                    enrollment_id,
                    subject=subject,
                    teacher=teacher,
                    start=start,
                    end=end,
                    include_submitted=True,
                )

                payload["awaiting_marks"] = [
                    r for r in rows
                    if r["status_tag"] == "submitted"
                ]

            # =====================================
            # DUE RANGE (this week / any window)
            # =====================================

            elif focus == "due_range":

                if not (start or end):

                    monday = today - timedelta(
                        days=today.weekday()
                    )

                    start = monday

                    end = monday + timedelta(days=6)

                rows = await repo.get_pending_homework(
                    enrollment_id,
                    subject=subject,
                    teacher=teacher,
                    start=start,
                    end=end,
                    include_submitted=True,
                )

                payload["due_window"] = {
                    "start": (
                        start.isoformat()
                        if start
                        else None
                    ),
                    "end": (
                        end.isoformat()
                        if end
                        else None
                    ),
                }

                wstart = payload["due_window"]["start"]

                wend = payload["due_window"]["end"]

                if wstart and wend:

                    range_label = (
                        f"Between {wstart} and {wend}"
                    )

                elif wend:

                    range_label = f"Before {wend}"

                elif wstart:

                    range_label = f"After {wstart}"

                else:

                    range_label = ""

                payload["due_window"]["label"] = (
                    range_label
                )

                payload["pending"] = [
                    r for r in rows
                    if r["status_tag"] == "pending"
                ]

                payload["overdue"] = [
                    r for r in rows
                    if r["status_tag"] == "overdue"
                ]

                payload["resubmit"] = [
                    r for r in rows
                    if r["status_tag"] == "resubmit_requested"
                ]

                payload["submitted"] = [
                    r for r in rows
                    if r["status_tag"] in ("submitted", "graded")
                ]

            # =====================================
            # UPCOMING (due from tomorrow onward)
            # =====================================

            elif focus == "upcoming":

                start = today + timedelta(days=1)

                rows = await repo.get_pending_homework(
                    enrollment_id,
                    subject=subject,
                    teacher=teacher,
                    start=start,
                )

                payload["upcoming"] = [
                    r for r in rows
                    if r["status_tag"] == "pending"
                ]

            # =====================================
            # NEXT UP
            # =====================================

            elif focus == "next_up":

                rows = await repo.get_pending_homework(
                    enrollment_id,
                    subject=subject,
                    teacher=teacher,
                    start=start,
                    end=end,
                )

                nxt = next(
                    (
                        r for r in rows
                        if (
                            r.get("due_date")
                            and r["due_date"].date() > today
                            and r["status_tag"] != "resubmit_requested"
                        )
                    ),
                    None,
                )

                payload["next_up"] = nxt

                payload["overdue"] = [
                    r for r in rows
                    if r["status_tag"] == "overdue"
                ]

                payload["resubmit"] = [
                    r for r in rows
                    if r["status_tag"] == "resubmit_requested"
                ]

            # =====================================
            # GENERAL - one wide query, deduped
            # sections built in Python.
            # =====================================

            else:

                rows = await repo.get_pending_homework(
                    enrollment_id,
                    subject=subject,
                    teacher=teacher,
                    start=start,
                    end=end,
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

                payload["resubmit"] = [
                    r for r in rows
                    if r["status_tag"] == "resubmit_requested"
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
            + len(payload["resubmit"])
        )

        payload["overdue_count"] = (
            len(payload["overdue"])
        )

        payload["resubmit_count"] = (
            len(payload["resubmit"])
        )

        payload["awaiting_marks_count"] = (
            len(payload["awaiting_marks"])
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

        payload["upcoming_count"] = (
            len(payload["upcoming"])
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

        if payload.get("count_only"):

            if focus == "due_range":

                window = payload.get("due_window") or {}

                label = window.get("label")

                span = (
                    label.lower()
                    if label
                    else "in this period"
                )

                return (
                    f"{payload['pending_count']} unfinished "
                    f"homework assignment(s) {span}."
                )

            count_lines = {
                "pending":
                    f"You have {payload['pending_count']} pending "
                    f"homework assignment(s).",
                "overdue":
                    f"{payload['overdue_count']} homework "
                    f"assignment(s) are overdue.",
                "upcoming":
                    f"{payload['upcoming_count']} homework "
                    f"assignment(s) coming up.",
                "due_today":
                    f"{payload['due_today_count']} homework "
                    f"assignment(s) due today.",
                "due_tomorrow":
                    f"{payload['due_tomorrow_count']} homework "
                    f"assignment(s) due tomorrow.",
                "submitted":
                    f"You have handed in "
                    f"{payload['submitted_count']} homework "
                    f"assignment(s).",
                "graded":
                    f"{payload['graded_count']} homework "
                    f"assignment(s) have been graded.",
                "awaiting_marks":
                    f"{payload['awaiting_marks_count']} homework "
                    f"assignment(s) submitted but not yet graded.",
                "resubmit":
                    f"{payload['resubmit_count']} homework "
                    f"assignment(s) need to be resubmitted.",
                "general":
                    f"You have {payload['pending_count']} open "
                    f"homework assignment(s).",
            }

            return count_lines.get(focus)

        if focus == "pending":

            if pending:

                lines.append(
                    f"You have {len(pending)} pending "
                    f"homework assignment(s)."
                )

                for item in pending:

                    lines.append(
                        self.format_item_line(item)
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

                for item in overdue:

                    lines.append(
                        self.format_item_line(item)
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

                for item in rows:

                    stamp = (
                        format_datetime(item["submitted_at"])
                        if item.get("submitted_at")
                        else "date not recorded"
                    )

                    line = (
                        f"• {item['title']} - submitted {stamp}"
                    )

                    if (
                        item.get("status_tag") == "graded"
                        and item.get("marks_obtained") is not None
                    ):

                        pct = int(round(
                            float(item["marks_obtained"])
                            / float(item["total_marks"])
                            * 100
                        )) if item.get("total_marks") else 0

                        line += (
                            f" (graded: "
                            f"{int(round(float(item['marks_obtained'])))}/"
                            f"{int(round(float(item['total_marks'] or 0)))}"
                            f" ({pct}%))"
                        )

                    lines.append(line)

            if (
                payload.get("subject")
                and (
                    payload["pending"]
                    or payload["overdue"]
                    or payload["resubmit"]
                )
            ):

                lines.append("")

                lines.append(
                    "Still pending for "
                    f"{payload['subject']}:"
                )

                for item in (
                    payload["overdue"]
                    + payload["pending"]
                    + payload["resubmit"]
                ):

                    lines.append(
                        self.format_item_line(item)
                    )

            elif not rows:

                lines.append(
                    "You haven't submitted any homework "
                    "matching that yet."
                )

        elif focus == "awaiting_marks":

            rows = payload["awaiting_marks"]

            if rows:

                lines.append(
                    f"{len(rows)} homework assignment(s) "
                    f"submitted but not yet graded:"
                )

                for item in rows:

                    stamp = (
                        format_datetime(item["submitted_at"])
                        if item.get("submitted_at")
                        else "date not recorded"
                    )

                    lines.append(
                        f"• {item['title']} - submitted {stamp}"
                    )

            else:

                lines.append(
                    "No submitted homework is awaiting marks."
                )

        elif focus == "graded":

            rows = payload["graded"]

            if rows:

                lines.append(
                    f"{len(rows)} homework assignment(s) "
                    f"have been graded:"
                )

                for item in rows:

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

        elif focus == "resubmit":

            rows = payload["resubmit"]

            if rows:

                lines.append(
                    f"{len(rows)} homework assignment(s) "
                    f"need to be resubmitted:"
                )

                for item in rows:

                    lines.append(
                        self.format_item_line(item)
                    )

            else:

                lines.append(
                    "No homework is waiting for resubmission."
                )

        elif focus == "due_range":

            window = payload.get("due_window") or {}

            range_label = window.get("label") or ""

            listed = (
                pending
                + overdue
                + payload["resubmit"]
            )

            if listed:

                lines.append(
                    f"{range_label} there are "
                    f"{len(listed)} unfinished assignment(s)"
                    + (
                        f" and {payload['submitted_count']} handed in."
                        if payload["submitted"]
                        else "."
                    )
                )

                for item in listed:

                    lines.append(
                        self.format_item_line(item)
                    )

            else:

                lines.append(
                    f"No homework was due {range_label.lower()}."
                    if range_label
                    else "No homework was due in this period."
                )

        elif focus == "upcoming":

            rows = payload["upcoming"]

            if rows:

                lines.append(
                    f"{len(rows)} homework assignment(s) "
                    f"coming up:"
                )

                for item in rows:

                    lines.append(
                        f"• {item['title']} - "
                        f"due {str(item['due_date'])[:10]}."
                    )

            else:

                lines.append(
                    "No homework is coming up."
                )

        elif focus == "next_up":

            nxt = payload["next_up"]

            if nxt:

                lines.append(
                    f"{nxt['title']} comes first - "
                    f"due {str(nxt['due_date'])[:10]}."
                )

            else:

                overdue = payload["overdue"]
                resubmit = payload["resubmit"]

                bits = []

                if overdue:

                    bits.append(
                        f"{len(overdue)} overdue"
                    )

                if resubmit:

                    bits.append(
                        f"{len(resubmit)} resubmission(s)"
                    )

                if bits:

                    lines.append(
                        "No upcoming homework right now, but "
                        "you have "
                        + " and ".join(bits)
                        + " to handle."
                    )

                else:

                    lines.append(
                        "Nothing is coming due - you're all "
                        "caught up."
                    )

        else:

            # GENERAL

            if payload.get("conversational"):

                total_open = payload["pending_count"]

                lines.append(
                    f"You have {total_open} open assignment(s): "
                    f"{len(overdue)} overdue, "
                    f"{len(pending)} still upcoming"
                    + (
                        f", {len(payload['resubmit'])} resubmit"
                        if payload["resubmit"]
                        else ""
                    )
                    + "."
                )

                if len(overdue):

                    lines.append(
                        "Complete overdue homework first."
                    )

                return "\n".join(lines)

            total_open = (
                payload["pending_count"]
            )

            if total_open:

                lines.append(
                    f"You have {total_open} open assignment(s): "
                    f"{len(overdue)} overdue, "
                    f"{len(pending)} still upcoming"
                    + (
                        f", {len(payload['resubmit'])} "
                        + (
                            "resubmission requested"
                            if len(payload["resubmit"]) == 1
                            else "resubmissions requested"
                        )
                        if payload["resubmit"]
                        else ""
                    )
                    + "."
                )

                if overdue:

                    lines.append("")
                    lines.append("Overdue:")

                    for item in overdue:

                        lines.append(
                            self.format_item_line(item)
                        )

                if pending:

                    lines.append("")
                    lines.append("Pending:")

                    for item in pending:

                        lines.append(
                            self.format_item_line(item)
                        )

                if payload["resubmit"]:

                    lines.append("")
                    lines.append("Resubmission requested:")

                    for item in payload["resubmit"]:

                        lines.append(
                            self.format_item_line(item)
                        )

                if payload.get("subject"):

                    if payload["submitted"]:

                        lines.append("")
                        lines.append("Handed in:")

                        for item in payload["submitted"]:

                            lines.append(
                                self.format_item_line(item)
                            )

                    if payload["graded"]:

                        lines.append("")
                        lines.append("Graded:")

                        for item in payload["graded"]:

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
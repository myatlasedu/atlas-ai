from db.session import (
    AsyncSessionLocal
)

from db.repositories.student.topic_repository import (
    TopicRepository
)

from core.marks_privacy import (
    performance_withheld_message,
    redact_tool_payload,
)


def build_grouped_list(
    topics,
    header,
    include_scores=False,
):
    if not topics:
        return None

    by_subject = {}

    for t in topics:

        subj = t["subject_name"]

        if subj not in by_subject:
            by_subject[subj] = []

        by_subject[subj].append(t)

    lines = [header]

    for subj, items in by_subject.items():

        # include_scores is retained for call-site compatibility, but topic
        # averages are marks-derived and are never printed.

        names = ", ".join(
            t["topic_name"]
            for t in items
        )

        lines.append(f"- {subj}: {names}")

    return "\n".join(lines)


class TopicTool:

    async def run(
        self,
        context,
        parsed_intent,
    ):

        # Topic averages are derived from marks, so they never leave the tool.

        return redact_tool_payload(
            await self._run(
                context,
                parsed_intent,
            )
        )

    async def _run(
        self,
        context,
        parsed_intent,
    ):

        if not context.enrollment_id:

            return {
                "error":
                    "Enrollment ID missing"
            }

        query = (
            getattr(
                parsed_intent,
                "original_query",
                ""
            )
            .lower()
            .replace("?", "")
            .replace(".", "")
            .strip()
        )

        subject_name = getattr(
            parsed_intent,
            "subject",
            None,
        )

        topic_name = getattr(
            parsed_intent,
            "topic",
            None,
        )

        async with AsyncSessionLocal() as db:

            repo = TopicRepository(
                db
            )

            statistics = (
                await repo.get_topic_statistics(
                    context.enrollment_id,
                    subject_name=subject_name,
                    topic_name=topic_name,
                )
            )

            completed_topics = (
                statistics[
                    "completed_topics"
                ]
            )

            pending_topics = (
                statistics[
                    "pending_topics"
                ]
            )

            all_topics = (
                statistics[
                    "all_topics"
                ]
            )

            payload = {

                "module":
                    "topic",

                "completed_topic_count":
                    len(
                        completed_topics
                    ),

                "pending_topic_count":
                    len(
                        pending_topics
                    ),

                "total_topic_count":
                    len(
                        all_topics
                    ),

                "completed_topics":
                    completed_topics,

                "pending_topics":
                    pending_topics,

                # weak_topics / strong_topics are ranked by marks-derived
                # averages, so they are kept local and never put on the
                # payload or in the LLM context.

                "llm_context": {

                    "status":

                        (
                            "building"
                            if not all_topics
                            else "available"
                        ),

                    "metrics": {

                        "total_topics":
                            len(
                                all_topics
                            ),

                        "completed_topics":
                            len(
                                completed_topics
                            ),

                        "pending_topics":
                            len(
                                pending_topics
                            ),

                    },

                    "highlights": [

                        (
                            f"You have completed "
                            f"{len(completed_topics)} "
                            f"topic(s)."
                        ),

                        (
                            f"{len(pending_topics)} "
                            f"topic(s) are still "
                            f"pending."
                        ),

                    ],

                    "actions": [

                        "Complete pending topics."
                    ],
                }
            }

            # =====================================
            # KEYWORD DETECTION
            # =====================================

            has_topic = any(
                w in query
                for w in ["topic", "topics"]
            )

            has_completed = any(
                w in query
                for w in [
                    "completed", "covered",
                    "finished", "done",
                ]
            )

            has_pending = any(
                w in query
                for w in [
                    "pending", "remaining",
                    "left", "not yet covered",
                    "not covered",
                ]
            )

            has_weak = any(
                w in query
                for w in [
                    "weak", "struggling",
                    "difficult", "improve",
                    "revision", "revise",
                    "focus",
                ]
            )

            has_strong = any(
                w in query
                for w in [
                    "strong", "best",
                    "good", "doing well",
                    "performing well",
                    "strongest",
                ]
            )

            has_all = any(
                w in query
                for w in [
                    "all", "every",
                    "full", "complete",
                    "list", "show",
                    "display", "see",
                    "overview", "summary",
                    "progress",
                ]
            )

            # =====================================
            # COMPLETED TOPICS
            # =====================================

            if has_topic and has_completed:

                result = build_grouped_list(
                    completed_topics,
                    (
                        f"You have completed "
                        f"{len(completed_topics)} "
                        f"topic(s):"
                    ),
                )

                payload[
                    "llm_context"
                ][
                    "completed_topics_list"
                ] = (
                    result
                    or "No topics have been "
                       "completed yet."
                )

                return payload

            # =====================================
            # PENDING TOPICS
            # =====================================

            if has_topic and has_pending:

                result = build_grouped_list(
                    pending_topics,
                    (
                        f"You have "
                        f"{len(pending_topics)} "
                        f"topic(s) pending:"
                    ),
                )

                payload[
                    "llm_context"
                ][
                    "pending_topics_list"
                ] = (
                    result
                    or "No pending topics. "
                       "All topics are completed."
                )

                return payload

            # =====================================
            # WEAK / STRONG TOPICS
            # =====================================
            #
            # Both lists are ranked by marks-derived averages, so naming the
            # topics discloses where the student scored badly or well.

            if has_topic and (has_weak or has_strong):

                payload[
                    "direct_answer"
                ] = performance_withheld_message(
                    getattr(context, "role", "student")
                )

                return payload

            # =====================================
            # SPECIFIC TOPIC
            # =====================================

            if getattr(
                parsed_intent,
                "topic",
                None,
            ):

                topic_name_lower = (
                    getattr(
                        parsed_intent,
                        "topic",
                        "",
                    )
                    .lower()
                )

                all_scored = (
                    completed_topics
                    + pending_topics
                )

                specific = [
                    t
                    for t in all_scored
                    if topic_name_lower
                    in t["topic_name"].lower()
                ]

                seen_ids = set()
                unique = []
                for t in specific:
                    if (
                        t["topic_id"]
                        not in seen_ids
                    ):
                        seen_ids.add(
                            t["topic_id"]
                        )
                        unique.append(t)

                if unique:

                    topic = unique[0]

                    status = (
                        "completed"
                        if topic["completed"]
                        else "pending"
                    )

                    lines = [
                        (
                            f"{topic['topic_name']} "
                            f"({topic['subject_name']})"
                        ),
                        f"Status: {status}",
                    ]


                    payload[
                        "llm_context"
                    ][
                        "specific_topic"
                    ] = (
                        "\n".join(lines)
                    )

                else:

                    payload[
                        "llm_context"
                    ][
                        "specific_topic"
                    ] = (
                        f"Topic "
                        f"'{topic_name_lower}' "
                        f"not found."
                    )

                return payload

            # =====================================
            # ALL TOPICS
            # =====================================

            if has_topic and has_all:

                total_count = len(all_topics)
                comp_count = len(completed_topics)
                pend_count = len(pending_topics)

                total_word = (
                    "topic"
                    if total_count == 1
                    else "topics"
                )

                comp_word = (
                    "topic"
                    if comp_count == 1
                    else "topics"
                )

                pend_word = (
                    "topic"
                    if pend_count == 1
                    else "topics"
                )

                # Curriculum coverage only - the weak/strong split is ranked
                # by marks-derived averages and is never reported.

                topic_summary = (
                    f"You have "
                    f"{total_count} "
                    f"{total_word} total:\n"
                    f"- {comp_count} "
                    f"completed\n"
                    f"- {pend_count} "
                    f"pending"
                )

                payload[
                    "llm_context"
                ][
                    "topic_summary"
                ] = topic_summary

                completed_list = (
                    build_grouped_list(
                        completed_topics,
                        "Completed topics:",
                    )
                    or "No topics completed yet."
                )

                pending_list = (
                    build_grouped_list(
                        pending_topics,
                        "Pending topics:",
                    )
                    or "No pending topics."
                )

                payload[
                    "llm_context"
                ][
                    "completed_topics_list"
                ] = completed_list

                payload[
                    "llm_context"
                ][
                    "pending_topics_list"
                ] = pending_list

                return payload

            # =====================================
            # DEFAULT
            # =====================================

            payload[
                "llm_context"
            ][
                "fallback_note"
            ] = (
                "Here is your overall "
                "topic progress:"
            )

            payload[
                "topic_analysis"
            ] = True

            return payload

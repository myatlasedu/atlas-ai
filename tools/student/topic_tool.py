from db.session import (
    AsyncSessionLocal
)

from db.repositories.student.topic_repository import (
    TopicRepository
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

        if include_scores:

            names = ", ".join(
                f"{t['topic_name']}"
                f" ({t['average_score']}%)"
                for t in items
            )

        else:

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

            weak_topics = (
                statistics[
                    "weak_topics"
                ]
            )

            strong_topics = (
                statistics[
                    "strong_topics"
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

                "weak_topic_count":
                    len(
                        weak_topics
                    ),

                "strong_topic_count":
                    len(
                        strong_topics
                    ),

                "total_topic_count":
                    len(
                        all_topics
                    ),

                "completed_topics":
                    completed_topics,

                "pending_topics":
                    pending_topics,

                "weak_topics":
                    weak_topics,

                "strong_topics":
                    strong_topics,

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

                        "weak_topics":
                            len(
                                weak_topics
                            ),

                        "strong_topics":
                            len(
                                strong_topics
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

                        (
                            f"{len(weak_topics)} "
                            f"topic(s) currently "
                            f"need revision."
                        ),
                    ],

                    "focus": [

                        topic["topic_name"]

                        for topic in weak_topics[:5]
                    ],

                    "actions": [

                        "Revise weak topics.",

                        "Complete pending topics."
                    ],
                    "weak_topics_detail": [
                        {
                            "subject_name":
                                t["subject_name"],
                            "topic_name":
                                t["topic_name"],
                            "average_score":
                                t.get(
                                    "average_score"
                                ),
                            "homework_average":
                                t.get(
                                    "homework_average"
                                ),
                            "assessment_average":
                                t.get(
                                    "assessment_average"
                                ),
                        }
                        for t in weak_topics
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
            # WEAK TOPICS
            # =====================================

            if has_topic and has_weak:

                result = build_grouped_list(
                    weak_topics,
                    (
                        f"You have "
                        f"{len(weak_topics)} "
                        f"weak topic(s) that "
                        f"need revision:"
                    ),
                    include_scores=True,
                )

                payload[
                    "llm_context"
                ][
                    "weak_topics_list"
                ] = (
                    result
                    or "No weak topics "
                       "were identified."
                )

                return payload

            # =====================================
            # STRONG TOPICS
            # =====================================

            if has_topic and has_strong:

                result = build_grouped_list(
                    strong_topics,
                    (
                        f"You are doing well "
                        f"in "
                        f"{len(strong_topics)} "
                        f"topic(s):"
                    ),
                    include_scores=True,
                )

                payload[
                    "llm_context"
                ][
                    "strong_topics_list"
                ] = (
                    result
                    or "No strong topics "
                       "were identified."
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

                    if (
                        topic["average_score"]
                        is not None
                    ):
                        lines.append(
                            f"Average score: "
                            f"{topic['average_score']}%"
                        )

                    if (
                        topic["homework_average"]
                        is not None
                    ):
                        lines.append(
                            f"Homework average: "
                            f"{topic['homework_average']}%"
                        )

                    if (
                        topic["assessment_average"]
                        is not None
                    ):
                        lines.append(
                            f"Assessment average: "
                            f"{topic['assessment_average']}%"
                        )

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
                weak_count = len(weak_topics)
                strong_count = len(strong_topics)

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

                weak_line = (
                    f"- {weak_count} "
                    f"needs revision (weak)"
                    if weak_count == 1
                    else f"- {weak_count} "
                    f"need revision (weak)"
                )

                strong_line = (
                    f"- {strong_count} "
                    f"is strong"
                    if strong_count == 1
                    else f"- {strong_count} "
                    f"are strong"
                )

                topic_summary = (
                    f"You have "
                    f"{total_count} "
                    f"{total_word} total:\n"
                    f"- {comp_count} "
                    f"completed\n"
                    f"- {pend_count} "
                    f"pending"
                )

                if weak_count or strong_count:
                    topic_summary += (
                        "\n\nOut of "
                        "scored topics:\n"
                    )
                    if weak_count:
                        topic_summary += (
                            weak_line + "\n"
                        )
                    if strong_count:
                        topic_summary += (
                            strong_line
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

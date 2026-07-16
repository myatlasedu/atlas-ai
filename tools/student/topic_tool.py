from db.session import (
    AsyncSessionLocal
)

from db.repositories.student.topic_repository import (
    TopicRepository
)


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
            .strip()
        )

        async with AsyncSessionLocal() as db:

            repo = TopicRepository(
                db
            )

            statistics = (
                await repo.get_topic_statistics(
                    context.enrollment_id
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
                    },

                    "highlights": [

                        (
                            f"You have completed {len(completed_topics)} topic(s)."
                        ),

                        (
                            f"{len(pending_topics)} topic(s) are still pending."
                        ),

                        (
                            f"{len(weak_topics)} topic(s) currently need revision."
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
                }
            }

            # =====================================
            # COMPLETED TOPICS
            # =====================================

            if any(

                phrase in query

                for phrase in [

                    "completed topic",
                    "completed topics",
                    "covered topics",
                    "topics covered",
                    "finished topics",
                    "what have i completed",
                ]
            ):

                payload[
                    "direct_answer"
                ] = (

                    f"You have completed "
                    f"{len(completed_topics)} "
                    f"topic(s)."
                )

                return payload

            # =====================================
            # PENDING TOPICS
            # =====================================

            if any(

                phrase in query

                for phrase in [

                    "pending topic",
                    "pending topics",
                    "remaining topics",
                    "topics left",
                    "what topics are left",
                    "what should i study next",
                ]
            ):

                payload[
                    "direct_answer"
                ] = (

                    f"You still have "
                    f"{len(pending_topics)} "
                    f"topic(s) pending."
                )

                return payload

            # =====================================
            # WEAK TOPICS
            # =====================================

            if any(

                phrase in query

                for phrase in [

                    "weak topic",
                    "weak topics",
                    "revision",
                    "revise",
                    "focus on",
                    "struggling",
                    "difficult topic",
                    "improve",
                ]
            ):

                if weak_topics:

                    payload[
                        "direct_answer"
                    ] = (

                        f"You currently have "
                        f"{len(weak_topics)} "
                        f"weak topic(s) that "
                        f"need revision."
                    )

                else:

                    payload[
                        "direct_answer"
                    ] = (

                        "No weak topics "
                        "were identified."
                    )

                return payload

            # =====================================
            # ALL TOPICS
            # =====================================

            if any(

                phrase in query

                for phrase in [

                    "topics",
                    "topic summary",
                    "topic overview",
                    "list topics",
                    "all topics",
                ]
            ):

                payload[
                    "direct_answer"
                ] = (

                    f"You currently have "
                    f"{len(all_topics)} topic(s), "
                    f"of which "
                    f"{len(completed_topics)} "
                    f"are completed and "
                    f"{len(pending_topics)} "
                    f"are pending."
                )

                return payload

            # =====================================
            # DEFAULT
            # =====================================

            payload[
                "topic_analysis"
            ] = True

            return payload
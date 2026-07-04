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
        parsed_intent
    ):

        query = (
            getattr(
                parsed_intent,
                "original_query",
                ""
            )
            .lower()
        )

        async with AsyncSessionLocal() as db:

            repo = TopicRepository(
                db
            )

            assessment_topics = (
                await repo.get_assessment_topics(
                    context.enrollment_id
                )
            )

            weak_topics = (
                await repo.get_weak_topics(
                    context.enrollment_id
                )
            )

            payload = {

                "module":
                    "topic",

                "assessment_topic_count":
                    len(
                        assessment_topics
                    ),

                "weak_topic_count":
                    len(
                        weak_topics
                    ),

                "assessment_topics":
                    assessment_topics,

                "weak_topics":
                    weak_topics
            }

            #
            # Weak topic queries
            #

            if any(
                phrase in query
                for phrase in [
                    "weak topic",
                    "weak topics",
                    "struggling",
                    "improve",
                    "focus on",
                    "difficult topic",
                    "revision",
                    "revise"
                ]
            ):

                if weak_topics:

                    payload[
                        "direct_answer"
                    ] = (
                        f"You currently have "
                        f"{len(weak_topics)} "
                        f"weak topic(s) identified "
                        f"from recent assessments "
                        f"and homework."
                    )

                else:

                    payload[
                        "direct_answer"
                    ] = (
                        "No weak topics were "
                        "identified in the last "
                        "30 days."
                    )

                return payload

            #
            # Assessment topic queries
            #

            if any(
                phrase in query
                for phrase in [
                    "assessment topics",
                    "exam topics",
                    "tested topics",
                    "topics assessed",
                    "study next"
                ]
            ):

                if assessment_topics:

                    payload[
                        "direct_answer"
                    ] = (
                        f"There are "
                        f"{len(assessment_topics)} "
                        f"topic(s) that have appeared "
                        f"in your assessments."
                    )

                else:

                    payload[
                        "direct_answer"
                    ] = (
                        "No assessment topics "
                        "were found."
                    )

                return payload

            #
            # Default topic analysis
            #

            payload[
                "topic_analysis"
            ] = True

            return payload
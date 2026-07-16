from db.session import (
    AsyncSessionLocal,
)

from db.repositories.student.subject_repository import (
    SubjectRepository,
)

from llm.builders.subject_builder import (
    build_subject_llm_context,
)

class SubjectTool:

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
                "",
            )
            .lower()
            .replace("?", "")
            .replace(".", "")
            .strip()
        )

        async with AsyncSessionLocal() as db:

            repo = SubjectRepository(
                db
            )

            payload = await repo.get_subject_performance(
                context.enrollment_id
            )

            payload["module"] = "subject"

            payload["llm_context"] = (
                build_subject_llm_context(
                    payload
                )
            )

            strongest = payload.get(
                "strongest_subject"
            )

            weakest = payload.get(
                "weakest_subject"
            )

            subjects = payload.get(
                "subjects",
                [],
            )

            # =====================================
            # SUBJECT ANALYSIS
            # =====================================

            if any(
                phrase in query
                for phrase in [

                    "analyze my subject performance",
                    "analyse my subject performance",

                    "how am i doing across subjects",

                    "subject performance",

                    "subject analysis",

                    "subject insights",

                    "why is my weakest subject weak",

                    "why is my weakest subject",

                    "improve my weakest subject",

                    "how can i improve my weakest subject",

                    "what should i improve in subjects",

                    "what subject should i focus on",

                    "how can i improve my subject performance",

                    "subject strengths",

                    "subject weaknesses",

                    "how am i doing in subjects",
                ]
            ):

                payload["subject_analysis"] = True

                return payload

            # =====================================
            # STRONGEST SUBJECT
            # =====================================

            if any(
                phrase in query
                for phrase in [

                    "strongest subject",

                    "best subject",

                    "highest scoring subject",

                    "top subject",
                ]
            ):

                payload["direct_answer"] = (

                    f"Your strongest subject is "

                    f"{strongest['subject_name']} "

                    f"with a score of "

                    f"{strongest['score']}."

                    if strongest

                    else

                    "No subject data available."
                )

                return payload

            # =====================================
            # WEAKEST SUBJECT
            # =====================================

            if any(
                phrase in query
                for phrase in [

                    "weakest subject",

                    "worst subject",

                    "lowest scoring subject",

                    "needs attention",
                ]
            ):

                payload["direct_answer"] = (

                    f"Your weakest subject is "

                    f"{weakest['subject_name']} "

                    f"with a score of "

                    f"{weakest['score']}."

                    if weakest

                    else

                    "No subject data available."
                )

                return payload

            # =====================================
            # SUBJECT COMPARISON
            # =====================================

            if any(
                phrase in query
                for phrase in [

                    "compare my subjects",

                    "compare subjects",
                ]
            ):

                payload["direct_answer"] = (

                    f"You have {payload['subject_count']} subjects. "

                    f"Your strongest subject is "

                    f"{strongest['subject_name']} "

                    f"and your weakest subject is "

                    f"{weakest['subject_name']}."

                    if subjects

                    else

                    "No subject data available."
                )

                return payload

            # =====================================
            # SUBJECT SUMMARY
            # =====================================

            if any(
                phrase in query
                for phrase in [

                    "subject summary",

                    "subject overview",

                    "my subjects",
                ]
            ):

                payload["direct_answer"] = (

                    f"You currently study "

                    f"{payload['subject_count']} subjects. "

                    f"Your average score is "

                    f"{payload['average_score']}%. "

                    f"Your strongest subject is "

                    f"{strongest['subject_name']} "

                    f"and your weakest subject is "

                    f"{weakest['subject_name']}."

                    if subjects

                    else

                    "No subject data available."
                )

                return payload

            # =====================================
            # DEFAULT
            # =====================================

            payload["subject_analysis"] = True

            return payload
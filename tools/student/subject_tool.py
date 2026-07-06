from db.session import (
    AsyncSessionLocal
)

from db.repositories.student.subject_repository import (
    SubjectRepository
)


class SubjectTool:

    async def run(
        self,
        context,
        parsed_intent
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

        async with AsyncSessionLocal() as db:

            repo = SubjectRepository(
                db
            )

            subjects = (
                await repo.get_subject_performance(
                    context.enrollment_id
                )
            )

            strongest = (
                await repo.get_strongest_subject(
                    context.enrollment_id
                )
            )

            weakest = (
                await repo.get_weakest_subject(
                    context.enrollment_id
                )
            )

            insights = []

            recommended_focus = []

            if weakest:

                insights.append(
                    f"{weakest['subject_name']} "
                    f"is currently the lowest "
                    f"scoring subject."
                )

                recommended_focus.append(
                    weakest["subject_name"]
                )

            payload = {

                "module":
                    "subject",

                "subjects":
                    subjects,

                "strongest_subject":
                    strongest,

                "weakest_subject":
                    weakest,

                "insights":
                    insights,

                "recommended_focus":
                    recommended_focus
            }

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

                    "how am i doing in subjects"
                ]
            ):

                payload[
                    "subject_analysis"
                ] = True

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
                    "top subject"
                ]
            ):

                if strongest:

                    payload[
                        "direct_answer"
                    ] = (
                        f"Your strongest subject "
                        f"is "
                        f"{strongest['subject_name']} "
                        f"with a score of "
                        f"{strongest['score']}."
                    )

                else:

                    payload[
                        "direct_answer"
                    ] = (
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
                    "needs attention"
                ]
            ):

                if weakest:

                    payload[
                        "direct_answer"
                    ] = (
                        f"Your weakest subject "
                        f"is "
                        f"{weakest['subject_name']} "
                        f"with a score of "
                        f"{weakest['score']}."
                    )

                else:

                    payload[
                        "direct_answer"
                    ] = (
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
                    "compare subjects"
                ]
            ):

                if subjects:

                    payload[
                        "direct_answer"
                    ] = (
                        f"You have "
                        f"{len(subjects)} subjects. "
                        f"Strongest: "
                        f"{strongest['subject_name']}. "
                        f"Weakest: "
                        f"{weakest['subject_name']}."
                    )

                else:

                    payload[
                        "direct_answer"
                    ] = (
                        "No subject data available."
                    )

                return payload

            # =====================================
            # SUBJECT SUMMARY / OVERVIEW
            # =====================================

            if any(
                phrase in query
                for phrase in [
                    "subject summary",
                    "subject overview",
                    "my subjects"
                ]
            ):

                if subjects:

                    payload[
                        "direct_answer"
                    ] = (
                        f"You currently have "
                        f"{len(subjects)} subjects. "
                        f"Your strongest subject is "
                        f"{strongest['subject_name']} "
                        f"and your weakest subject is "
                        f"{weakest['subject_name']}."
                    )

                else:

                    payload[
                        "direct_answer"
                    ] = (
                        "No subject data available."
                    )

                return payload

            # =====================================
            # DEFAULT
            # =====================================

            payload[
                "subject_analysis"
            ] = True

            return payload
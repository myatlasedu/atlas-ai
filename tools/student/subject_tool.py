from db.session import (
    AsyncSessionLocal,
)

from db.repositories.student.subject_repository import (
    SubjectRepository,
)

from llm.builders.subject_builder import (
    build_subject_llm_context,
)

from core.marks_privacy import (
    performance_withheld_message,
    redact_tool_payload,
)

class SubjectTool:

    async def run(
        self,
        context,
        parsed_intent,
    ):

        # Subject scores are marks-derived, so they never leave the tool.

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

                payload[
                    "direct_answer"
                ] = performance_withheld_message(
                    getattr(context, "role", "student")
                )

                return payload

            # =====================================
            # STRONGEST / WEAKEST / COMPARISON
            # =====================================
            #
            # Every one of these ranks subjects by a marks-derived score, so
            # naming a subject discloses where the student scored well or badly.

            if any(
                phrase in query
                for phrase in [

                    "strongest subject",

                    "best subject",

                    "highest scoring subject",

                    "top subject",

                    "weakest subject",

                    "worst subject",

                    "lowest scoring subject",

                    "needs attention",

                    "compare my subjects",

                    "compare subjects",
                ]
            ):

                payload[
                    "direct_answer"
                ] = performance_withheld_message(
                    getattr(context, "role", "student")
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

                    f"{payload['subject_count']} subject(s)."

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
from db.session import (
    AsyncSessionLocal
)

from db.repositories.mentor.assessment_repository import (
    MentorAssessmentRepository
)

from sqlalchemy import text

class AssessmentTool:

    async def run(
        self,
        context,
        parsed_intent
    ):

        async with AsyncSessionLocal() as db:

            repo = MentorAssessmentRepository(
                db
            )

            view = (
                parsed_intent.view
                or "summary"
            )

            if view == "summary":

                return await repo.get_summary(
                    context=context,
                    parsed_intent=parsed_intent
                )

            if view == "upcoming_assessments":

                return await repo.get_upcoming_assessments(
                    context=context,
                    parsed_intent=parsed_intent
                )

            if view == "pending_grading":

                return await repo.get_pending_grading(
                    context=context,
                    parsed_intent=parsed_intent
                )

            if view == "subject_statistics":

                return await repo.get_subject_statistics(
                    context=context,
                    parsed_intent=parsed_intent
                )
            
            if view == "pending_grading":

                return await repo.get_pending_grading(
                    context=context,
                    parsed_intent=parsed_intent
                )

            if view == "low_scores":

                return await repo.get_low_scores(
                    context=context,
                    parsed_intent=parsed_intent
                )
            
            if view == "top_performers":

                return await repo.get_top_performers(
                    context=context,
                    parsed_intent=parsed_intent
                )
            
            if view == "upcoming_assessments":

                return await repo.get_upcoming_assessments(
                    context=context,
                    parsed_intent=parsed_intent
                )
            
            if view == "subject_statistics":

                return await repo.get_subject_statistics(
                    context=context,
                    parsed_intent=parsed_intent
                )
            
            return await repo.get_summary(
                context=context,
                parsed_intent=parsed_intent
            )
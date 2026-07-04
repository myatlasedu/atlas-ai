from db.session import (
    AsyncSessionLocal
)

from db.repositories.mentor.homework_repository import (
    MentorHomeworkRepository
)


class HomeworkTool:

    async def run(
        self,
        context,
        parsed_intent
    ):

        async with AsyncSessionLocal() as db:

            repo = MentorHomeworkRepository(
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

            if view == "overdue_homework":

                return await repo.get_overdue_homework(
                    context=context,
                    parsed_intent=parsed_intent
                )

            if view == "submitted_homework":

                return await repo.get_submitted_homework(
                    context=context,
                    parsed_intent=parsed_intent
                )

            if view == "not_submitted_homework":

                return await repo.get_not_submitted_homework(
                    context=context,
                    parsed_intent=parsed_intent
                )
            
            if view == "pending_homework":

                return await repo.get_pending_homeworks(
                    context=context,
                    parsed_intent=parsed_intent
                )
            
            if view == "overdue_homework":

                return await repo.get_overdue_homeworks(
                    context=context,
                    parsed_intent=parsed_intent
                )
            
            if view == "not_submitted_homework":

                return await repo.get_not_submitted_students(
                    context=context,
                    parsed_intent=parsed_intent
                )
            
            if view == "awaiting_review":

                return await repo.get_awaiting_review(
                    context=context,
                    parsed_intent=parsed_intent
                )
            
            if view == "homework_feedback":

                return await repo.get_homework_feedback(
                    context=context,
                    parsed_intent=parsed_intent
                )
            
            if view == "due_today":

                return await repo.get_due_today(
                    context=context,
                    parsed_intent=parsed_intent
                )

            return await repo.get_summary(
                context=context,
                parsed_intent=parsed_intent
            )
        
    
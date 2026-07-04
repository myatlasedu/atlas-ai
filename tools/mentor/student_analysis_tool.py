import asyncio

from db.session import (
    AsyncSessionLocal
)

from db.repositories.mentor.attendance_repository import (
    MentorAttendanceRepository
)

from db.repositories.mentor.homework_repository import (
    MentorHomeworkRepository
)

from db.repositories.mentor.assessment_repository import (
    MentorAssessmentRepository
)

from services.risk_calculator import (
    RiskCalculator
)

class StudentAnalysisTool:

    async def run(
        self,
        context,
        parsed_intent
    ):

        async with AsyncSessionLocal() as db:

            attendance_repo = (
                MentorAttendanceRepository(db)
            )

            homework_repo = (
                MentorHomeworkRepository(db)
            )

            assessment_repo = (
                MentorAssessmentRepository(db)
            )

            view = (
                parsed_intent.view
                or
                "at_risk_students"
            )

            if view == "at_risk_students":

                return await self.get_at_risk_students(

                    attendance_repo=attendance_repo,

                    homework_repo=homework_repo,

                    assessment_repo=assessment_repo,

                    context=context,

                    parsed_intent=parsed_intent
                )

            return await self.get_at_risk_students(

                attendance_repo=attendance_repo,

                homework_repo=homework_repo,

                assessment_repo=assessment_repo,

                context=context,

                parsed_intent=parsed_intent
            )

    async def get_at_risk_students(
        self,
        attendance_repo,
        homework_repo,
        assessment_repo,
        context,
        parsed_intent
    ):

        attendance = await attendance_repo.get_student_risk_data(
            context=context,
            parsed_intent=parsed_intent
        )

        homework = await homework_repo.get_student_risk_data(
            context=context,
            parsed_intent=parsed_intent
        )

        assessment = await assessment_repo.get_student_risk_data(
            context=context,
            parsed_intent=parsed_intent
        )
 
        students = {}

        # =====================================
        # Attendance
        # =====================================

        for student in attendance:

            students.setdefault(

                student["id"],

                {}
            ).update(student)

        # =====================================
        # Homework
        # =====================================

        for student in homework:

            students.setdefault(

                student["id"],

                {}
            ).update(student)

        # =====================================
        # Assessment
        # =====================================

        for student in assessment:

            students.setdefault(

                student["id"],

                {}
            ).update(student)

        high = 0
        medium = 0
        low = 0

        results = []

        for student in students.values():

            risk = RiskCalculator.calculate(
                student
            )

            student.update(
                risk
            )

            results.append(student)

        results.sort(

            key=lambda student: (

                -student["risk_score"],

                student["name"]
            )
        )

        return {

            "module":
                "student_analysis",

            "total_students":
                len(results),

            "high_risk_students":
                high,

            "medium_risk_students":
                medium,

            "low_risk_students":
                low,

            "students":
                results
        }
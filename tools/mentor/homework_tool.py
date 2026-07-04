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
        
    async def get_student_risk_data(
        self,
        context,
        parsed_intent
    ):

        query = """
        SELECT

            s.id,

            s.first_name,
            s.middle_name,
            s.last_name,

            s.admission_number,

            g.name AS grade,

            sec.name AS section,

            COUNT(DISTINCT h.id) AS assigned_homeworks,

            COUNT(DISTINCT CASE
                WHEN hs.id IS NOT NULL
                THEN h.id
            END) AS submitted_homeworks,

            COUNT(DISTINCT CASE
                WHEN hs.id IS NULL
                THEN h.id
            END) AS pending_homeworks,

            COUNT(DISTINCT CASE
                WHEN hs.id IS NULL
                AND h.due_date < NOW()
                THEN h.id
            END) AS overdue_homeworks

        FROM students_homeworkstudentmap hsm

        INNER JOIN students_homework h
            ON h.id = hsm.homework_id

        INNER JOIN students_studentenrollment se
            ON se.id = hsm.enrollment_id

        INNER JOIN students_student s
            ON s.id = se.student_id

        INNER JOIN schools_academicclass ac
            ON ac.id = se.academic_class_id

        INNER JOIN schools_grade g
            ON g.id = ac.grade_id

        INNER JOIN schools_section sec
            ON sec.id = ac.section_id

        LEFT JOIN students_homeworksubmission hs
            ON hs.homework_id = h.id
            AND hs.enrollment_id = se.id

        WHERE

            h.subject_offering_id IN (

                SELECT id

                FROM schools_subjectoffering

                WHERE

                    teacher_id = :staff_id
            )

        AND

            se.academic_year_id = :academic_year_id
        """

        params = {

            "staff_id":
                context.staff_id,

            "academic_year_id":
                context.academic_year_id
        }

        if parsed_intent.start_date:

            query += """

            AND h.created_at::date >= :start_date
            """

            params["start_date"] = (
                parsed_intent.start_date
            )

        if parsed_intent.end_date:

            query += """

            AND h.created_at::date <= :end_date
            """

            params["end_date"] = (
                parsed_intent.end_date
            )

        if parsed_intent.grade:

            query += """

            AND g.name = :grade
            """

            params["grade"] = (
                parsed_intent.grade
            )

        if parsed_intent.section:

            query += """

            AND sec.name = :section
            """

            params["section"] = (
                parsed_intent.section
            )

        query += """

        GROUP BY

            s.id,

            s.first_name,
            s.middle_name,
            s.last_name,

            s.admission_number,

            g.id,
            g.name,
            g."order",

            sec.id,
            sec.name,
            sec.display_order

        ORDER BY

            g."order",

            sec.display_order,

            s.first_name,

            s.last_name
        """

        result = await self.db.execute(
            text(query),
            params
        )

        students = []

        for row in result.mappings():

            row = dict(row)

            row["name"] = " ".join(

                filter(

                    None,

                    [

                        row.pop("first_name"),

                        row.pop("middle_name"),

                        row.pop("last_name")
                    ]
                )
            )

            students.append(row)

        return students
        
    
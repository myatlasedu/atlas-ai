from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class MentorHomeworkRepository:

    def __init__(
        self,
        db: AsyncSession
    ):
        self.db = db

    async def get_summary(
        self,
        context,
        parsed_intent
    ):

        query = """
        WITH homework_stats AS (

            SELECT

                h.id,

                h.title,

                h.due_date,

                COUNT(DISTINCT hsm.enrollment_id) AS assigned_students,

                COUNT(DISTINCT hs.enrollment_id) AS submitted_students

            FROM students_homework h

            INNER JOIN schools_subjectoffering so
                ON so.id = h.subject_offering_id

            LEFT JOIN students_homeworkstudentmap hsm
                ON hsm.homework_id = h.id

            LEFT JOIN students_homeworksubmission hs
                ON hs.homework_id = h.id
               AND hs.enrollment_id = hsm.enrollment_id

            INNER JOIN schools_academicclass ac
                ON ac.id = so.academic_class_id

            INNER JOIN schools_grade g
                ON g.id = ac.grade_id

            INNER JOIN schools_section sec
                ON sec.id = ac.section_id

            WHERE

                so.teacher_id = :staff_id

            AND

                ac.academic_year_id = :academic_year_id
        """

        params = {

            "staff_id":
                context.staff_id,

            "academic_year_id":
                context.academic_year_id
        }

        if parsed_intent.grade:

            query += """

            AND g.name = :grade
            """

            params["grade"] = parsed_intent.grade

        if parsed_intent.section:

            query += """

            AND sec.name = :section
            """

            params["section"] = parsed_intent.section

        if parsed_intent.start_date:

            query += """

            AND h.created_at::date >= :start_date
            """

            params["start_date"] = parsed_intent.start_date

        if parsed_intent.end_date:

            query += """

            AND h.created_at::date <= :end_date
            """

            params["end_date"] = parsed_intent.end_date

        query += """

            GROUP BY

                h.id,
                h.title,
                h.due_date
        )

        SELECT

            COUNT(*) AS total_homeworks,

            COUNT(*) FILTER (

                WHERE assigned_students = submitted_students

                AND assigned_students > 0

            ) AS completed_homeworks,

            COUNT(*) FILTER (

                WHERE assigned_students > submitted_students

            ) AS pending_homeworks,

            COUNT(*) FILTER (

                WHERE

                    due_date IS NOT NULL

                AND

                    due_date < NOW()

                AND

                    assigned_students > submitted_students

            ) AS overdue_homeworks,

            COALESCE(
                SUM(assigned_students),
                0
            ) AS assigned_students,

            COALESCE(
                SUM(submitted_students),
                0
            ) AS submitted_students

        FROM homework_stats
        """

        result = await self.db.execute(
            text(query),
            params
        )

        row = result.mappings().first()

        assigned = row["assigned_students"] or 0

        submitted = row["submitted_students"] or 0

        pending = assigned - submitted

        percentage = 0

        if assigned:

            percentage = round(
                (submitted / assigned) * 100,
                2
            )

        return {

            "module": "homework",

            "total_homeworks":
                row["total_homeworks"] or 0,

            "completed_homeworks":
                row["completed_homeworks"] or 0,

            "pending_homeworks":
                row["pending_homeworks"] or 0,

            "overdue_homeworks":
                row["overdue_homeworks"] or 0,

            "assigned_students":
                assigned,

            "submitted_students":
                submitted,

            "pending_students":
                pending,

            "submission_percentage":
                percentage
        }
    
    async def get_pending_homeworks(
        self,
        context,
        parsed_intent
    ):

        query = """
        SELECT

            h.id,

            h.title,

            h.due_date,

            sub.name AS subject,

            g.name AS grade,

            sec.name AS section,

            COUNT(DISTINCT hsm.enrollment_id) AS assigned_students,

            COUNT(DISTINCT hs.enrollment_id) AS submitted_students,

            (
                COUNT(DISTINCT hsm.enrollment_id)
                -
                COUNT(DISTINCT hs.enrollment_id)
            ) AS pending_students

        FROM students_homework h

        INNER JOIN schools_subjectoffering so
            ON so.id = h.subject_offering_id

        INNER JOIN schools_subjectversion sv
            ON sv.id = so.subject_version_id

        INNER JOIN schools_subject sub
            ON sub.id = sv.subject_id

        INNER JOIN schools_academicclass ac
            ON ac.id = so.academic_class_id

        INNER JOIN schools_grade g
            ON g.id = ac.grade_id

        INNER JOIN schools_section sec
            ON sec.id = ac.section_id

        INNER JOIN students_homeworkstudentmap hsm
            ON hsm.homework_id = h.id

        LEFT JOIN students_homeworksubmission hs
            ON hs.homework_id = h.id
            AND hs.enrollment_id = hsm.enrollment_id

        WHERE

            so.teacher_id = :staff_id

        AND

            ac.academic_year_id = :academic_year_id
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

            params["start_date"] = parsed_intent.start_date

        if parsed_intent.end_date:

            query += """

            AND h.created_at::date <= :end_date
            """

            params["end_date"] = parsed_intent.end_date

        if parsed_intent.grade:

            query += """

            AND g.name = :grade
            """

            params["grade"] = parsed_intent.grade

        if parsed_intent.section:

            query += """

            AND sec.name = :section
            """

            params["section"] = parsed_intent.section

        if parsed_intent.subject:

            query += """

            AND sub.name = :subject
            """

            params["subject"] = parsed_intent.subject

        query += """

        GROUP BY

            h.id,
            h.title,
            h.due_date,

            sub.id,
            sub.name,

            g.id,
            g.name,
            g."order",

            sec.id,
            sec.name,
            sec.display_order

        HAVING

            COUNT(DISTINCT hs.enrollment_id)
            <
            COUNT(DISTINCT hsm.enrollment_id)

        ORDER BY

            h.due_date NULLS LAST,

            g."order",

            sec.display_order,

            h.title
        """

        result = await self.db.execute(
            text(query),
            params
        )

        homeworks = []

        for row in result.mappings():

            homeworks.append(
                dict(row)
            )

        return {

            "module": "homework",

            "homework_count": len(homeworks),

            "homeworks": homeworks
        }
    
    async def get_overdue_homeworks(
        self,
        context,
        parsed_intent
    ):

        query = """
        SELECT

            h.id,

            h.title,

            h.due_date,

            sub.name AS subject,

            g.name AS grade,

            sec.name AS section,

            COUNT(DISTINCT hsm.enrollment_id) AS assigned_students,

            COUNT(DISTINCT hs.enrollment_id) AS submitted_students,

            (
                COUNT(DISTINCT hsm.enrollment_id)
                -
                COUNT(DISTINCT hs.enrollment_id)
            ) AS pending_students

        FROM students_homework h

        INNER JOIN schools_subjectoffering so
            ON so.id = h.subject_offering_id

        INNER JOIN schools_subjectversion sv
            ON sv.id = so.subject_version_id

        INNER JOIN schools_subject sub
            ON sub.id = sv.subject_id

        INNER JOIN schools_academicclass ac
            ON ac.id = so.academic_class_id

        INNER JOIN schools_grade g
            ON g.id = ac.grade_id

        INNER JOIN schools_section sec
            ON sec.id = ac.section_id

        INNER JOIN students_homeworkstudentmap hsm
            ON hsm.homework_id = h.id

        LEFT JOIN students_homeworksubmission hs
            ON hs.homework_id = h.id
            AND hs.enrollment_id = hsm.enrollment_id

        WHERE

            so.teacher_id = :staff_id

        AND

            ac.academic_year_id = :academic_year_id

        AND

            h.due_date IS NOT NULL

        AND

            h.due_date < NOW()
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

            params["start_date"] = parsed_intent.start_date

        if parsed_intent.end_date:

            query += """

            AND h.created_at::date <= :end_date
            """

            params["end_date"] = parsed_intent.end_date

        if parsed_intent.grade:

            query += """

            AND g.name = :grade
            """

            params["grade"] = parsed_intent.grade

        if parsed_intent.section:

            query += """

            AND sec.name = :section
            """

            params["section"] = parsed_intent.section

        if parsed_intent.subject:

            query += """

            AND sub.name = :subject
            """

            params["subject"] = parsed_intent.subject

        query += """

        GROUP BY

            h.id,
            h.title,
            h.due_date,

            sub.id,
            sub.name,

            g.id,
            g.name,
            g."order",

            sec.id,
            sec.name,
            sec.display_order

        HAVING

            COUNT(DISTINCT hs.enrollment_id)
            <
            COUNT(DISTINCT hsm.enrollment_id)

        ORDER BY

            h.due_date,

            g."order",

            sec.display_order,

            h.title
        """

        result = await self.db.execute(
            text(query),
            params
        )

        homeworks = []

        for row in result.mappings():

            homeworks.append(
                dict(row)
            )

        return {

            "module": "homework",

            "homework_count": len(homeworks),

            "homeworks": homeworks
        }
    
    async def get_not_submitted_students(
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

            h.id AS homework_id,

            h.title,

            h.due_date,

            sub.name AS subject,

            g.name AS grade,

            sec.name AS section

        FROM students_homeworkstudentmap hsm

        INNER JOIN students_homework h
            ON h.id = hsm.homework_id

        INNER JOIN schools_subjectoffering so
            ON so.id = h.subject_offering_id

        INNER JOIN schools_subjectversion sv
            ON sv.id = so.subject_version_id

        INNER JOIN schools_subject sub
            ON sub.id = sv.subject_id

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
            AND hs.enrollment_id = hsm.enrollment_id

        WHERE

            so.teacher_id = :staff_id

        AND

            ac.academic_year_id = :academic_year_id

        AND

            hs.id IS NULL
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

            params["start_date"] = parsed_intent.start_date

        if parsed_intent.end_date:

            query += """

            AND h.created_at::date <= :end_date
            """

            params["end_date"] = parsed_intent.end_date

        if parsed_intent.grade:

            query += """

            AND g.name = :grade
            """

            params["grade"] = parsed_intent.grade

        if parsed_intent.section:

            query += """

            AND sec.name = :section
            """

            params["section"] = parsed_intent.section

        if parsed_intent.subject:

            query += """

            AND sub.name = :subject
            """

            params["subject"] = parsed_intent.subject

        query += """

        ORDER BY

            h.due_date NULLS LAST,

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

        return {

            "module": "homework",

            "student_count": len(students),

            "students": students
        }
    
    async def get_awaiting_review(
        self,
        context,
        parsed_intent
    ):

        query = """
        SELECT

            hs.id,

            h.id AS homework_id,

            h.title,

            h.due_date,

            s.id AS student_id,

            s.first_name,
            s.middle_name,
            s.last_name,

            s.admission_number,

            sub.name AS subject,

            g.name AS grade,

            sec.name AS section,

            hs.submitted_at,

            hs.status,

            hs.marks_obtained,

            hs.teacher_note,

            hs.reviewed_at

        FROM students_homeworksubmission hs

        INNER JOIN students_homework h
            ON h.id = hs.homework_id

        INNER JOIN students_studentenrollment se
            ON se.id = hs.enrollment_id

        INNER JOIN students_student s
            ON s.id = se.student_id

        INNER JOIN schools_subjectoffering so
            ON so.id = h.subject_offering_id

        INNER JOIN schools_subjectversion sv
            ON sv.id = so.subject_version_id

        INNER JOIN schools_subject sub
            ON sub.id = sv.subject_id

        INNER JOIN schools_academicclass ac
            ON ac.id = se.academic_class_id

        INNER JOIN schools_grade g
            ON g.id = ac.grade_id

        INNER JOIN schools_section sec
            ON sec.id = ac.section_id

        WHERE

            so.teacher_id = :staff_id

        AND

            ac.academic_year_id = :academic_year_id

        AND

            hs.reviewed_at IS NULL
        """

        params = {

            "staff_id":
                context.staff_id,

            "academic_year_id":
                context.academic_year_id
        }

        if parsed_intent.grade:

            query += """

            AND g.name = :grade
            """

            params["grade"] = parsed_intent.grade

        if parsed_intent.section:

            query += """

            AND sec.name = :section
            """

            params["section"] = parsed_intent.section

        if parsed_intent.subject:

            query += """

            AND sub.name = :subject
            """

            params["subject"] = parsed_intent.subject

        if parsed_intent.start_date:

            query += """

            AND hs.submitted_at::date >= :start_date
            """

            params["start_date"] = parsed_intent.start_date

        if parsed_intent.end_date:

            query += """

            AND hs.submitted_at::date <= :end_date
            """

            params["end_date"] = parsed_intent.end_date

        query += """

        ORDER BY

            hs.submitted_at,

            g."order",

            sec.display_order,

            s.first_name
        """

        result = await self.db.execute(
            text(query),
            params
        )

        submissions = []

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

            submissions.append(row)

        return {

            "module": "homework",

            "submission_count": len(submissions),

            "submissions": submissions
        }
    
    async def get_homework_feedback(
        self,
        context,
        parsed_intent
    ):

        query = """
        SELECT

            hs.id,

            h.id AS homework_id,

            h.title,

            h.due_date,

            s.id AS student_id,

            s.first_name,
            s.middle_name,
            s.last_name,

            s.admission_number,

            sub.name AS subject,

            g.name AS grade,

            sec.name AS section,

            hs.teacher_note,

            hs.marks_obtained,

            hs.reviewed_at,

            hs.submitted_at,

            hs.status

        FROM students_homeworksubmission hs

        INNER JOIN students_homework h
            ON h.id = hs.homework_id

        INNER JOIN students_studentenrollment se
            ON se.id = hs.enrollment_id

        INNER JOIN students_student s
            ON s.id = se.student_id

        INNER JOIN schools_subjectoffering so
            ON so.id = h.subject_offering_id

        INNER JOIN schools_subjectversion sv
            ON sv.id = so.subject_version_id

        INNER JOIN schools_subject sub
            ON sub.id = sv.subject_id

        INNER JOIN schools_academicclass ac
            ON ac.id = se.academic_class_id

        INNER JOIN schools_grade g
            ON g.id = ac.grade_id

        INNER JOIN schools_section sec
            ON sec.id = ac.section_id

        WHERE

            so.teacher_id = :staff_id

        AND

            ac.academic_year_id = :academic_year_id

        AND

            hs.status = 2
        """

        params = {

            "staff_id":
                context.staff_id,

            "academic_year_id":
                context.academic_year_id
        }

        if parsed_intent.grade:

            query += """

            AND g.name = :grade
            """

            params["grade"] = parsed_intent.grade

        if parsed_intent.section:

            query += """

            AND sec.name = :section
            """

            params["section"] = parsed_intent.section

        if parsed_intent.subject:

            query += """

            AND sub.name = :subject
            """

            params["subject"] = parsed_intent.subject

        if parsed_intent.start_date:

            query += """

            AND hs.reviewed_at::date >= :start_date
            """

            params["start_date"] = parsed_intent.start_date

        if parsed_intent.end_date:

            query += """

            AND hs.reviewed_at::date <= :end_date
            """

            params["end_date"] = parsed_intent.end_date

        query += """

        ORDER BY

            hs.reviewed_at DESC,

            g."order",

            sec.display_order,

            s.first_name,

            s.last_name
        """

        result = await self.db.execute(
            text(query),
            params
        )

        feedback = []

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

            feedback.append(row)

        return {

            "module": "homework",

            "feedback_count": len(feedback),

            "feedback": feedback
        }
    
    async def get_due_today(
        self,
        context,
        parsed_intent
    ):

        query = """
        SELECT

            h.id,

            h.title,

            h.due_date,

            sub.name AS subject,

            g.name AS grade,

            sec.name AS section,

            COUNT(DISTINCT hsm.enrollment_id) AS assigned_students,

            COUNT(DISTINCT hs.enrollment_id) AS submitted_students,

            (
                COUNT(DISTINCT hsm.enrollment_id)
                -
                COUNT(DISTINCT hs.enrollment_id)
            ) AS pending_students

        FROM students_homework h

        INNER JOIN schools_subjectoffering so
            ON so.id = h.subject_offering_id

        INNER JOIN schools_subjectversion sv
            ON sv.id = so.subject_version_id

        INNER JOIN schools_subject sub
            ON sub.id = sv.subject_id

        INNER JOIN schools_academicclass ac
            ON ac.id = so.academic_class_id

        INNER JOIN schools_grade g
            ON g.id = ac.grade_id

        INNER JOIN schools_section sec
            ON sec.id = ac.section_id

        INNER JOIN students_homeworkstudentmap hsm
            ON hsm.homework_id = h.id

        LEFT JOIN students_homeworksubmission hs
            ON hs.homework_id = h.id
            AND hs.enrollment_id = hsm.enrollment_id

        WHERE

            so.teacher_id = :staff_id

        AND

            ac.academic_year_id = :academic_year_id

        AND

            h.due_date IS NOT NULL

        AND

            h.due_date::date = CURRENT_DATE
        """

        params = {

            "staff_id":
                context.staff_id,

            "academic_year_id":
                context.academic_year_id
        }

        if parsed_intent.grade:

            query += """

            AND g.name = :grade
            """

            params["grade"] = parsed_intent.grade

        if parsed_intent.section:

            query += """

            AND sec.name = :section
            """

            params["section"] = parsed_intent.section

        if parsed_intent.subject:

            query += """

            AND sub.name = :subject
            """

            params["subject"] = parsed_intent.subject

        query += """

        GROUP BY

            h.id,
            h.title,
            h.due_date,

            sub.id,
            sub.name,

            g.id,
            g.name,
            g."order",

            sec.id,
            sec.name,
            sec.display_order

        ORDER BY

            g."order",

            sec.display_order,

            h.title
        """

        result = await self.db.execute(
            text(query),
            params
        )

        homeworks = []

        for row in result.mappings():

            homeworks.append(
                dict(row)
            )

        return {

            "module": "homework",

            "homework_count": len(homeworks),

            "homeworks": homeworks
        }
    
    async def get_submission_statistics(
        self,
        context,
        parsed_intent
    ):

        query = """
        SELECT

            sub.name AS subject,

            g.name AS grade,

            sec.name AS section,

            COUNT(DISTINCT h.id) AS homework_count,

            COUNT(DISTINCT hsm.enrollment_id) AS assigned_students,

            COUNT(DISTINCT hs.id) AS submitted_students

        FROM students_homework h

        INNER JOIN schools_subjectoffering so
            ON so.id = h.subject_offering_id

        INNER JOIN schools_subjectversion sv
            ON sv.id = so.subject_version_id

        INNER JOIN schools_subject sub
            ON sub.id = sv.subject_id

        INNER JOIN schools_academicclass ac
            ON ac.id = so.academic_class_id

        INNER JOIN schools_grade g
            ON g.id = ac.grade_id

        INNER JOIN schools_section sec
            ON sec.id = ac.section_id

        INNER JOIN students_homeworkstudentmap hsm
            ON hsm.homework_id = h.id

        LEFT JOIN students_homeworksubmission hs
            ON hs.homework_id = h.id
            AND hs.enrollment_id = hsm.enrollment_id

        WHERE

            so.teacher_id = :staff_id

        AND

            ac.academic_year_id = :academic_year_id
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

            params["start_date"] = parsed_intent.start_date

        if parsed_intent.end_date:

            query += """

            AND h.created_at::date <= :end_date
            """

            params["end_date"] = parsed_intent.end_date

        if parsed_intent.grade:

            query += """

            AND g.name = :grade
            """

            params["grade"] = parsed_intent.grade

        if parsed_intent.section:

            query += """

            AND sec.name = :section
            """

            params["section"] = parsed_intent.section

        query += """

        GROUP BY

            sub.id,
            sub.name,

            g.id,
            g.name,
            g."order",

            sec.id,
            sec.name,
            sec.display_order

        ORDER BY

            g."order",

            sec.display_order,

            sub.name
        """

        result = await self.db.execute(
            text(query),
            params
        )

        subjects = []

        total_homeworks = 0
        total_assigned = 0
        total_submitted = 0

        for row in result.mappings():

            row = dict(row)

            assigned = row["assigned_students"] or 0
            submitted = row["submitted_students"] or 0

            percentage = 0

            if assigned:

                percentage = round(
                    submitted * 100 / assigned,
                    2
                )

            row["submission_percentage"] = percentage

            total_homeworks += row["homework_count"] or 0
            total_assigned += assigned
            total_submitted += submitted

            subjects.append(row)

        overall = 0

        if total_assigned:

            overall = round(
                total_submitted * 100 / total_assigned,
                2
            )

        return {

            "module": "homework",

            "overall_submission_percentage": overall,

            "total_homeworks": total_homeworks,

            "assigned_students": total_assigned,

            "submitted_students": total_submitted,

            "subjects": subjects
        }
    
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
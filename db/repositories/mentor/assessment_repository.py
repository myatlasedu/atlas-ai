from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

class MentorAssessmentRepository:

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
        SELECT

            COUNT(DISTINCT a.id) AS total_assessments,

            COUNT(DISTINCT CASE
                WHEN a.is_published
                THEN a.id
            END) AS published_assessments,

            COUNT(DISTINCT CASE
                WHEN NOT a.is_published
                THEN a.id
            END) AS draft_assessments,

            COUNT(asr.id) AS student_records,

            COUNT(*) FILTER (
                WHERE asr.status = 2
            ) AS submitted,

            COUNT(*) FILTER (
                WHERE asr.status = 3
            ) AS graded,

            COUNT(*) FILTER (
                WHERE asr.status = 1
            ) AS not_submitted,

            COUNT(*) FILTER (
                WHERE asr.status = 4
            ) AS absent

        FROM students_assessment a

        INNER JOIN students_assessmentstudentrecord asr
            ON asr.assessment_id = a.id

        INNER JOIN schools_subjectoffering so
            ON so.id = a.subject_offering_id

        INNER JOIN schools_academicclass ac
            ON ac.id = a.academic_class_id

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

            AND a.assessment_date >= :start_date
            """

            params["start_date"] = parsed_intent.start_date

        if parsed_intent.end_date:

            query += """

            AND a.assessment_date <= :end_date
            """

            params["end_date"] = parsed_intent.end_date

        if parsed_intent.grade:

            query += """

            AND ac.grade_id IN (

                SELECT id

                FROM schools_grade

                WHERE name = :grade

            )
            """

            params["grade"] = parsed_intent.grade

        if parsed_intent.section:

            query += """

            AND ac.section_id IN (

                SELECT id

                FROM schools_section

                WHERE name = :section

            )
            """

            params["section"] = parsed_intent.section

        result = await self.db.execute(
            text(query),
            params
        )

        row = result.mappings().first()

        if not row:

            return {

                "module": "assessment",

                "total_assessments": 0,

                "published_assessments": 0,

                "draft_assessments": 0,

                "student_records": 0,

                "submitted": 0,

                "graded": 0,

                "not_submitted": 0,

                "absent": 0,

                "grading_percentage": 0
            }

        total = row["student_records"] or 0

        graded = row["graded"] or 0

        percentage = 0

        if total:

            percentage = round(
                graded * 100 / total,
                2
            )

        return {

            "module": "assessment",

            "total_assessments":
                row["total_assessments"] or 0,

            "published_assessments":
                row["published_assessments"] or 0,

            "draft_assessments":
                row["draft_assessments"] or 0,

            "student_records":
                total,

            "submitted":
                row["submitted"] or 0,

            "graded":
                graded,

            "not_submitted":
                row["not_submitted"] or 0,

            "absent":
                row["absent"] or 0,

            "grading_percentage":
                percentage
        }
    
    async def get_pending_grading(
        self,
        context,
        parsed_intent
    ):

        query = """
        SELECT

            asr.id,

            a.id AS assessment_id,

            a.title,

            a.assessment_date,

            a.total_marks,

            sub.name AS subject,

            g.name AS grade,

            sec.name AS section,

            s.id AS student_id,

            s.first_name,
            s.middle_name,
            s.last_name,

            s.admission_number,

            asr.status,

            asr.marks_obtained,

            asr.grade,

            asr.teacher_comment

        FROM students_assessmentstudentrecord asr

        INNER JOIN students_assessment a
            ON a.id = asr.assessment_id

        INNER JOIN students_studentenrollment se
            ON se.id = asr.enrollment_id

        INNER JOIN students_student s
            ON s.id = se.student_id

        INNER JOIN schools_subjectoffering so
            ON so.id = a.subject_offering_id

        INNER JOIN schools_subjectversion sv
            ON sv.id = so.subject_version_id

        INNER JOIN schools_subject sub
            ON sub.id = sv.subject_id

        INNER JOIN schools_academicclass ac
            ON ac.id = a.academic_class_id

        INNER JOIN schools_grade g
            ON g.id = ac.grade_id

        INNER JOIN schools_section sec
            ON sec.id = ac.section_id

        WHERE

            so.teacher_id = :staff_id

        AND

            ac.academic_year_id = :academic_year_id

        AND

            asr.status = 2
        """

        params = {

            "staff_id":
                context.staff_id,

            "academic_year_id":
                context.academic_year_id
        }

        if parsed_intent.start_date:

            query += """

            AND a.assessment_date >= :start_date
            """

            params["start_date"] = parsed_intent.start_date

        if parsed_intent.end_date:

            query += """

            AND a.assessment_date <= :end_date
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

            a.assessment_date,

            g."order",

            sec.display_order,

            s.first_name,

            s.last_name
        """

        result = await self.db.execute(
            text(query),
            params
        )

        records = []

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

            records.append(row)

        return {

            "module": "assessment",

            "submission_count": len(records),

            "submissions": records
        }
    
    async def get_low_scores(
        self,
        context,
        parsed_intent
    ):

        query = """
        SELECT

            asr.id,

            a.id AS assessment_id,

            a.title,

            a.assessment_date,

            a.total_marks,

            asr.marks_obtained,

            ROUND(
                (asr.marks_obtained * 100.0) /
                NULLIF(a.total_marks, 0),
                2
            ) AS percentage,

            asr.grade,

            asr.teacher_comment,

            s.id AS student_id,

            s.first_name,
            s.middle_name,
            s.last_name,

            s.admission_number,

            sub.name AS subject,

            g.name AS grade_name,

            sec.name AS section

        FROM students_assessmentstudentrecord asr

        INNER JOIN students_assessment a
            ON a.id = asr.assessment_id

        INNER JOIN students_studentenrollment se
            ON se.id = asr.enrollment_id

        INNER JOIN students_student s
            ON s.id = se.student_id

        INNER JOIN schools_subjectoffering so
            ON so.id = a.subject_offering_id

        INNER JOIN schools_subjectversion sv
            ON sv.id = so.subject_version_id

        INNER JOIN schools_subject sub
            ON sub.id = sv.subject_id

        INNER JOIN schools_academicclass ac
            ON ac.id = a.academic_class_id

        INNER JOIN schools_grade g
            ON g.id = ac.grade_id

        INNER JOIN schools_section sec
            ON sec.id = ac.section_id

        WHERE

            so.teacher_id = :staff_id

        AND

            ac.academic_year_id = :academic_year_id

        AND

            asr.status = 3

        AND

            a.total_marks > 0

        AND

            (
                (asr.marks_obtained * 100.0)
                /
                a.total_marks
            ) < 40
        """

        params = {

            "staff_id":
                context.staff_id,

            "academic_year_id":
                context.academic_year_id
        }

        if parsed_intent.start_date:

            query += """

            AND a.assessment_date >= :start_date
            """

            params["start_date"] = parsed_intent.start_date

        if parsed_intent.end_date:

            query += """

            AND a.assessment_date <= :end_date
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

            percentage,

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

            row["grade"] = row.pop("grade_name")

            students.append(row)

        return {

            "module": "assessment",

            "student_count": len(students),

            "students": students
        }
    
    async def get_top_performers(
        self,
        context,
        parsed_intent
    ):

        query = """
        SELECT

            asr.id,

            a.id AS assessment_id,

            a.title,

            a.assessment_date,

            a.total_marks,

            asr.marks_obtained,

            ROUND(
                (asr.marks_obtained * 100.0) /
                NULLIF(a.total_marks, 0),
                2
            ) AS percentage,

            asr.grade,

            asr.teacher_comment,

            s.id AS student_id,

            s.first_name,
            s.middle_name,
            s.last_name,

            s.admission_number,

            sub.name AS subject,

            g.name AS grade_name,

            sec.name AS section

        FROM students_assessmentstudentrecord asr

        INNER JOIN students_assessment a
            ON a.id = asr.assessment_id

        INNER JOIN students_studentenrollment se
            ON se.id = asr.enrollment_id

        INNER JOIN students_student s
            ON s.id = se.student_id

        INNER JOIN schools_subjectoffering so
            ON so.id = a.subject_offering_id

        INNER JOIN schools_subjectversion sv
            ON sv.id = so.subject_version_id

        INNER JOIN schools_subject sub
            ON sub.id = sv.subject_id

        INNER JOIN schools_academicclass ac
            ON ac.id = a.academic_class_id

        INNER JOIN schools_grade g
            ON g.id = ac.grade_id

        INNER JOIN schools_section sec
            ON sec.id = ac.section_id

        WHERE

            so.teacher_id = :staff_id

        AND

            ac.academic_year_id = :academic_year_id

        AND

            asr.status = 3

        AND

            a.total_marks > 0

        AND

            (
                (asr.marks_obtained * 100.0)
                /
                a.total_marks
            ) >= 90
        """

        params = {

            "staff_id":
                context.staff_id,

            "academic_year_id":
                context.academic_year_id
        }

        if parsed_intent.start_date:

            query += """

            AND a.assessment_date >= :start_date
            """

            params["start_date"] = parsed_intent.start_date

        if parsed_intent.end_date:

            query += """

            AND a.assessment_date <= :end_date
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

            percentage DESC,

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

            row["grade"] = row.pop("grade_name")

            students.append(row)

        return {

            "module": "assessment",

            "student_count": len(students),

            "students": students
        }
    
    async def get_upcoming_assessments(
        self,
        context,
        parsed_intent
    ):

        query = """
        SELECT

            a.id,

            a.title,

            a.description,

            a.assessment_date,

            a.total_marks,

            a.type,

            a.category,

            a.is_published,

            sub.name AS subject,

            g.name AS grade,

            sec.name AS section,

            COUNT(DISTINCT asr.enrollment_id) AS total_students,

            COUNT(DISTINCT CASE
                WHEN asr.status = 1
                THEN asr.enrollment_id
            END) AS pending_students,

            COUNT(DISTINCT CASE
                WHEN asr.status = 2
                THEN asr.enrollment_id
            END) AS submitted_students,

            COUNT(DISTINCT CASE
                WHEN asr.status = 3
                THEN asr.enrollment_id
            END) AS graded_students,

            COUNT(DISTINCT CASE
                WHEN asr.status = 4
                THEN asr.enrollment_id
            END) AS absent_students,

        FROM students_assessment a

        INNER JOIN schools_subjectoffering so
            ON so.id = a.subject_offering_id

        INNER JOIN schools_subjectversion sv
            ON sv.id = so.subject_version_id

        INNER JOIN schools_subject sub
            ON sub.id = sv.subject_id

        INNER JOIN schools_academicclass ac
            ON ac.id = a.academic_class_id

        INNER JOIN schools_grade g
            ON g.id = ac.grade_id

        INNER JOIN schools_section sec
            ON sec.id = ac.section_id

        LEFT JOIN students_assessmentstudentrecord asr
            ON asr.assessment_id = a.id

        WHERE

            so.teacher_id = :staff_id

        AND

            ac.academic_year_id = :academic_year_id

        AND

            a.assessment_date >= CURRENT_DATE
        """

        params = {

            "staff_id":
                context.staff_id,

            "academic_year_id":
                context.academic_year_id
        }

        if parsed_intent.start_date:

            query += """

            AND a.assessment_date >= :start_date
            """

            params["start_date"] = parsed_intent.start_date

        if parsed_intent.end_date:

            query += """

            AND a.assessment_date <= :end_date
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

            a.id,
            a.title,
            a.description,
            a.assessment_date,
            a.total_marks,

            sub.id,
            sub.name,

            g.id,
            g.name,
            g."order",

            sec.id,
            sec.name,
            sec.display_order

        ORDER BY

            a.assessment_date,

            g."order",

            sec.display_order,

            sub.name
        """

        result = await self.db.execute(
            text(query),
            params
        )

        assessments = []

        for row in result.mappings():

            row = dict(row)

            assessments.append(row)

        return {

            "module": "assessment",

            "assessment_count": len(assessments),

            "assessments": assessments
        }
    
    async def get_subject_statistics(
        self,
        context,
        parsed_intent
    ):

        query = """
        SELECT

            sub.name AS subject,

            g.name AS grade,

            sec.name AS section,

            COUNT(DISTINCT a.id) AS assessments,

            COUNT(asr.id) AS student_records,

            COUNT(*) FILTER (
                WHERE asr.status = 3
            ) AS graded,

            COUNT(*) FILTER (
                WHERE asr.status = 2
            ) AS submitted,

            COUNT(*) FILTER (
                WHERE asr.status = 1
            ) AS pending,

            COUNT(*) FILTER (
                WHERE asr.status = 4
            ) AS absent,

            ROUND(
                AVG(asr.marks_obtained)::numeric,
                2
            ) AS average_marks,

            ROUND(
                AVG(
                    (
                        asr.marks_obtained
                        * 100.0
                    )
                    /
                    NULLIF(
                        a.total_marks,
                        0
                    )
                )::numeric,
                2
            ) AS average_percentage,

        FROM students_assessment a

        INNER JOIN students_assessmentstudentrecord asr
            ON asr.assessment_id = a.id

        INNER JOIN schools_subjectoffering so
            ON so.id = a.subject_offering_id

        INNER JOIN schools_subjectversion sv
            ON sv.id = so.subject_version_id

        INNER JOIN schools_subject sub
            ON sub.id = sv.subject_id

        INNER JOIN schools_academicclass ac
            ON ac.id = a.academic_class_id

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

        if parsed_intent.start_date:

            query += """

            AND a.assessment_date >= :start_date
            """

            params["start_date"] = parsed_intent.start_date

        if parsed_intent.end_date:

            query += """

            AND a.assessment_date <= :end_date
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

        overall_records = 0
        overall_graded = 0

        for row in result.mappings():

            row = dict(row)

            records = row["student_records"] or 0
            graded = row["graded"] or 0

            grading_percentage = 0

            if records:

                grading_percentage = round(
                    graded * 100 / records,
                    2
                )

            row["grading_percentage"] = grading_percentage

            overall_records += records
            overall_graded += graded

            subjects.append(row)

        overall_percentage = 0

        if overall_records:

            overall_percentage = round(
                overall_graded * 100 / overall_records,
                2
            )

        return {

            "module": "assessment",

            "overall_grading_percentage":
                overall_percentage,

            "subjects":
                subjects
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

            COUNT(DISTINCT a.id) AS total_assessments,

            COUNT(DISTINCT CASE
                WHEN asr.status = 3
                THEN a.id
            END) AS graded_assessments,

            COUNT(DISTINCT CASE
                WHEN asr.status = 2
                THEN a.id
            END) AS submitted_assessments,

            COUNT(DISTINCT CASE
                WHEN asr.status = 1
                THEN a.id
            END) AS pending_assessments,

            COUNT(DISTINCT CASE
                WHEN asr.status = 4
                THEN a.id
            END) AS absent_assessments,

            ROUND(
                AVG(asr.marks_obtained)::numeric,
                2
            ) AS average_marks,

            ROUND(
                AVG(
                    (
                        asr.marks_obtained
                        * 100.0
                    )
                    /
                    NULLIF(
                        a.total_marks,
                        0
                    )
                )::numeric,
                2
            ) AS average_percentage,

            COUNT(*) FILTER (

                WHERE

                    asr.status = 3

                AND

                    (
                        (
                            asr.marks_obtained
                            * 100.0
                        )
                        /
                        NULLIF(
                            a.total_marks,
                            0
                        )
                    ) < 40

            ) AS low_score_count

        FROM students_assessmentstudentrecord asr

        INNER JOIN students_assessment a
            ON a.id = asr.assessment_id

        INNER JOIN students_studentenrollment se
            ON se.id = asr.enrollment_id

        INNER JOIN students_student s
            ON s.id = se.student_id

        INNER JOIN schools_subjectoffering so
            ON so.id = a.subject_offering_id

        INNER JOIN schools_academicclass ac
            ON ac.id = a.academic_class_id

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

        if parsed_intent.start_date:

            query += """

            AND a.assessment_date >= :start_date
            """

            params["start_date"] = (
                parsed_intent.start_date
            )

        if parsed_intent.end_date:

            query += """

            AND a.assessment_date <= :end_date
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

        if parsed_intent.subject:

            query += """

            AND so.subject_version_id IN (

                SELECT id

                FROM schools_subjectversion sv

                INNER JOIN schools_subject sub
                    ON sub.id = sv.subject_id

                WHERE

                    sub.name = :subject
            )
            """

            params["subject"] = (
                parsed_intent.subject
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

            students.append(
                row
            )

        return students
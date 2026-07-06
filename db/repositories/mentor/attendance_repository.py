
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class MentorAttendanceRepository:

    def __init__(
        self,
        db: AsyncSession
    ):
        self.db = db
    async def get_daily_summary(
        self,
        context,
        parsed_intent
    ):

        query = text(
            """
            SELECT

                COUNT(DISTINCT sa.enrollment_id) AS total_students,

                COUNT(DISTINCT CASE
                    WHEN sa.status = 1
                    THEN sa.enrollment_id
                END) AS present_students,

                COUNT(DISTINCT CASE
                    WHEN sa.status = 2
                    THEN sa.enrollment_id
                END) AS absent_students,

                COUNT(DISTINCT CASE
                    WHEN sa.status = 3
                    THEN sa.enrollment_id
                END) AS late_students,

                COUNT(DISTINCT CASE
                    WHEN sa.status = 4
                    THEN sa.enrollment_id
                END) AS half_day_students

            FROM students_studentattendance sa

            INNER JOIN students_studentenrollment se
                ON se.id = sa.enrollment_id

            WHERE

                se.academic_year_id = :academic_year_id

            AND

                sa.date BETWEEN :start_date
                            AND :end_date

            AND EXISTS (

                SELECT 1

                FROM students_studentperiodattendance spa

                INNER JOIN schools_periodsession ps
                    ON ps.id = spa.period_session_id

                WHERE

                    spa.enrollment_id = sa.enrollment_id

                AND

                    ps.date = sa.date

                AND

                    ps.actual_teacher_id = :staff_id
            )
            """
        )

        result = await self.db.execute(

            query,

            {

                "staff_id":
                    context.staff_id,

                "academic_year_id":
                    context.academic_year_id,

                "start_date":
                    parsed_intent.start_date,

                "end_date":
                    parsed_intent.end_date
            }
        )

        row = result.mappings().first()

        if not row:

            return {

                "total_students": 0,

                "present_students": 0,

                "absent_students": 0,

                "late_students": 0,

                "half_day_students": 0
            }

        return {

            "total_students":
                row["total_students"] or 0,

            "present_students":
                row["present_students"] or 0,

            "absent_students":
                row["absent_students"] or 0,

            "late_students":
                row["late_students"] or 0,

            "half_day_students":
                row["half_day_students"] or 0
        }

    async def get_regular_present_students(
        self,
        context,
        parsed_intent
    ):

        query = """
        SELECT DISTINCT ON (
            s.id,
            ps.date
        )

            s.id,

            s.first_name,
            s.middle_name,
            s.last_name,

            s.admission_number,

            g.name AS grade,

            sec.name AS section,

            ps.date,

            'regular' AS attendance_type

        FROM students_studentperiodattendance spa

        INNER JOIN schools_periodsession ps
            ON ps.id = spa.period_session_id

        INNER JOIN students_studentenrollment se
            ON se.id = spa.enrollment_id

        INNER JOIN students_student s
            ON s.id = se.student_id

        INNER JOIN schools_academicclass ac
            ON ac.id = se.academic_class_id

        INNER JOIN schools_grade g
            ON g.id = ac.grade_id

        INNER JOIN schools_section sec
            ON sec.id = ac.section_id

        WHERE

            ps.actual_teacher_id = :staff_id

        AND

            se.academic_year_id = :academic_year_id

        AND

            spa.status = 1

        AND

            ps.date BETWEEN :start_date
                        AND :end_date
        """

        params = {

            "staff_id":
                context.staff_id,

            "academic_year_id":
                context.academic_year_id,

            "start_date":
                parsed_intent.start_date,

            "end_date":
                parsed_intent.end_date
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

        query += """

        ORDER BY

            s.id,

            ps.date,

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
    
    async def get_half_day_students(
        self,
        context,
        parsed_intent
    ):

        students = await self.get_regular_half_day_students(
            context,
            parsed_intent
        )

        return {

            "module": "attendance",

            "student_count": len(students),

            "students": students
        }
    

    async def get_regular_late_students(
        self,
        context,
        parsed_intent
    ):

        query = """
        SELECT DISTINCT ON (
            s.id,
            ps.date
        )

            s.id,

            s.first_name,
            s.middle_name,
            s.last_name,

            s.admission_number,

            g.name AS grade,

            sec.name AS section,

            ps.date,

            'regular' AS attendance_type

        FROM students_studentperiodattendance spa

        INNER JOIN schools_periodsession ps
            ON ps.id = spa.period_session_id

        INNER JOIN students_studentenrollment se
            ON se.id = spa.enrollment_id

        INNER JOIN students_student s
            ON s.id = se.student_id

        INNER JOIN schools_timetableslot ts
            ON ts.id = ps.timetable_slot_id

        INNER JOIN schools_academicclass ac
            ON ac.id = ts.academic_class_id

        INNER JOIN schools_grade g
            ON g.id = ac.grade_id

        INNER JOIN schools_section sec
            ON sec.id = ac.section_id

        WHERE

            ps.actual_teacher_id = :staff_id

        AND

            se.academic_year_id = :academic_year_id

        AND

            spa.status = 3

        AND

            ps.date BETWEEN :start_date
                        AND :end_date
        """

        params = {

            "staff_id":
                context.staff_id,

            "academic_year_id":
                context.academic_year_id,

            "start_date":
                parsed_intent.start_date,

            "end_date":
                parsed_intent.end_date
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

        query += """

        ORDER BY

            s.id,

            ps.date,

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
    
    async def get_late_students(
        self,
        context,
        parsed_intent
    ):

        regular = await self.get_regular_late_students(
            context,
            parsed_intent
        )

        enrichment = await self.get_enrichment_late_students(
            context,
            parsed_intent
        )

        students = regular + enrichment

        students.sort(
            key=lambda x: (
                x["date"],
                x["grade"],
                x["section"],
                x["name"]
            )
        )

        return {

            "module": "attendance",

            "student_count": len(students),

            "students": students
        }

    async def get_present_students(
        self,
        context,
        parsed_intent
    ):

        regular = await self.get_regular_present_students(
            context,
            parsed_intent
        )

        enrichment = await self.get_enrichment_present_students(
            context,
            parsed_intent
        )

        students = regular + enrichment

        students.sort(
            key=lambda x: (
                x["date"],
                x["grade"],
                x["section"],
                x["name"]
            )
        )

        return {

            "module": "attendance",

            "student_count": len(students),

            "students": students
        }


    async def get_enrichment_absent_students(
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

            e.name AS grade,

            'Enrichment' AS section,

            es.session_date AS date,

            'enrichment' AS attendance_type

        FROM students_enrichmentattendance ea

        INNER JOIN schools_enrichmentsession es
            ON es.id = ea.session_id

        INNER JOIN schools_enrichmentoffering eo
            ON eo.id = es.enrichment_offering_id

        INNER JOIN schools_enrichment e
            ON e.id = eo.enrichment_id

        INNER JOIN students_studentenrollment se
            ON se.id = ea.enrollment_id

        INNER JOIN students_student s
            ON s.id = se.student_id

        WHERE

            eo.teacher_id = :staff_id

        AND

            eo.academic_year_id = :academic_year_id

        AND

            ea.status = 2

        AND

            es.session_date BETWEEN :start_date
                            AND :end_date

        ORDER BY

            es.session_date,

            s.first_name,

            s.last_name
        """

        result = await self.db.execute(

            text(query),

            {

                "staff_id":
                    context.staff_id,

                "academic_year_id":
                    context.academic_year_id,

                "start_date":
                    parsed_intent.start_date,

                "end_date":
                    parsed_intent.end_date
            }
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

    async def get_regular_absent_students(
        self,
        context,
        parsed_intent
    ):

        query = """
        SELECT DISTINCT ON (
            s.id,
            ps.date
        )

            s.id,

            s.first_name,
            s.middle_name,
            s.last_name,

            s.admission_number,

            g.name AS grade,

            sec.name AS section,

            ps.date,

            'regular' AS attendance_type

        FROM students_studentperiodattendance spa

        INNER JOIN schools_periodsession ps
            ON ps.id = spa.period_session_id

        INNER JOIN students_studentenrollment se
            ON se.id = spa.enrollment_id

        INNER JOIN students_student s
            ON s.id = se.student_id

        INNER JOIN schools_academicclass ac
            ON ac.id = se.academic_class_id

        INNER JOIN schools_grade g
            ON g.id = ac.grade_id

        INNER JOIN schools_section sec
            ON sec.id = ac.section_id

        WHERE

            ps.actual_teacher_id = :staff_id

        AND

            se.academic_year_id = :academic_year_id

        AND

            spa.status = 2

        AND

            ps.date BETWEEN :start_date
                        AND :end_date
        """

        params = {

            "staff_id":
                context.staff_id,

            "academic_year_id":
                context.academic_year_id,

            "start_date":
                parsed_intent.start_date,

            "end_date":
                parsed_intent.end_date
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

        query += """

        ORDER BY

            s.id,

            ps.date,

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

    async def get_absent_students(
        self,
        context,
        parsed_intent
    ):

        regular = await self.get_regular_absent_students(
            context,
            parsed_intent
        )

        enrichment = await self.get_enrichment_absent_students(
            context,
            parsed_intent
        )

        students = regular + enrichment

        students.sort(
            key=lambda x: (
                x["date"],
                x["grade"],
                x["section"],
                x["name"]
            )
        )

        return {

            "module": "attendance",

            "student_count": len(students),

            "students": students
        }

    async def get_enrichment_summary(
        self,
        context,
        parsed_intent
    ):

        query = """
        SELECT

            COUNT(*) AS total_students,

            SUM(
                CASE
                    WHEN ea.status = 1 THEN 1
                    ELSE 0
                END
            ) AS present_students,

            SUM(
                CASE
                    WHEN ea.status = 2 THEN 1
                    ELSE 0
                END
            ) AS absent_students,

            SUM(
                CASE
                    WHEN ea.status = 3 THEN 1
                    ELSE 0
                END
            ) AS late_students

        FROM students_enrichmentattendance ea

        INNER JOIN schools_enrichmentsession es
            ON es.id = ea.session_id

        INNER JOIN schools_enrichmentoffering eo
            ON eo.id = es.enrichment_offering_id

        INNER JOIN students_studentenrollment se
            ON se.id = ea.enrollment_id

        WHERE

            eo.teacher_id = :staff_id

        AND

            eo.academic_year_id = :academic_year_id

        AND

            es.session_date BETWEEN :start_date
                            AND :end_date
        """

        params = {

            "staff_id":
                context.staff_id,

            "academic_year_id":
                context.academic_year_id,

            "start_date":
                parsed_intent.start_date,

            "end_date":
                parsed_intent.end_date
        }

        result = await self.db.execute(
            text(query),
            params
        )

        row = result.mappings().first()

        if not row:

            return {

                "total_students": 0,

                "present_students": 0,

                "absent_students": 0,

                "late_students": 0
            }

        return {

            "total_students":
                row["total_students"] or 0,

            "present_students":
                row["present_students"] or 0,

            "absent_students":
                row["absent_students"] or 0,

            "late_students":
                row["late_students"] or 0
        }


    async def get_summary(
        self,
        context,
        parsed_intent
    ):

        regular = await self.get_regular_summary(
            context,
            parsed_intent
        )

        enrichment = await self.get_enrichment_summary(
            context,
            parsed_intent
        )

        total_students = (
            regular["total_students"]
            + enrichment["total_students"]
        )

        present_students = (
            regular["present_students"]
            + enrichment["present_students"]
        )

        absent_students = (
            regular["absent_students"]
            + enrichment["absent_students"]
        )

        late_students = (
            regular["late_students"]
            + enrichment["late_students"]
        )

        attendance_percentage = 0

        if total_students:

            attendance_percentage = round(
                (
                    present_students
                    + late_students
                )
                / total_students
                * 100,
                2
            )

        return {

            "module": "attendance",

            "regular": regular,

            "enrichment": enrichment,

            "overall": {

                "total_students":
                    total_students,

                "present_students":
                    present_students,

                "absent_students":
                    absent_students,

                "late_students":
                    late_students,

                "attendance_percentage":
                    attendance_percentage
            }
        }

    async def get_regular_summary(
        self,
        context,
        parsed_intent
    ):

        query = """
        WITH student_status AS (

            SELECT

                spa.enrollment_id,

                MAX(
                    CASE

                        WHEN spa.status = 2 THEN 3
                        WHEN spa.status = 3 THEN 2
                        WHEN spa.status = 1 THEN 1
                        ELSE 0

                    END
                ) AS final_status

            FROM students_studentperiodattendance spa

            INNER JOIN schools_periodsession ps
                ON ps.id = spa.period_session_id

            INNER JOIN students_studentenrollment se
                ON se.id = spa.enrollment_id

            INNER JOIN schools_timetableslot ts
                ON ts.id = ps.timetable_slot_id

            INNER JOIN schools_academicclass ac
                ON ac.id = ts.academic_class_id

            INNER JOIN schools_grade g
                ON g.id = ac.grade_id

            INNER JOIN schools_section sec
                ON sec.id = ac.section_id

            WHERE

                ps.actual_teacher_id = :staff_id

            AND

                se.academic_year_id = :academic_year_id

            AND

                ps.date BETWEEN :start_date
                            AND :end_date
        """

        params = {

            "staff_id": context.staff_id,
            "academic_year_id": context.academic_year_id,
            "start_date": parsed_intent.start_date,
            "end_date": parsed_intent.end_date
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

        query += """

            GROUP BY
                spa.enrollment_id

        )

        SELECT

            COUNT(*) AS total_students,

            COUNT(*) FILTER (
                WHERE final_status = 1
            ) AS present_students,

            COUNT(*) FILTER (
                WHERE final_status = 3
            ) AS absent_students,

            COUNT(*) FILTER (
                WHERE final_status = 2
            ) AS late_students

        FROM student_status
        """

        result = await self.db.execute(
            text(query),
            params
        )

        row = result.mappings().first()

        return {

            "total_students": row["total_students"] or 0,
            "present_students": row["present_students"] or 0,
            "absent_students": row["absent_students"] or 0,
            "late_students": row["late_students"] or 0
        }
    
    async def get_attendance_percentage(
        self,
        context,
        parsed_intent
    ):

        query = """
        SELECT

            COUNT(*) AS total_periods,

            COUNT(*) FILTER (
                WHERE spa.status = 1
            ) AS present_periods,

            COUNT(*) FILTER (
                WHERE spa.status = 2
            ) AS absent_periods,

            COUNT(*) FILTER (
                WHERE spa.status = 3
            ) AS late_periods

        FROM students_studentperiodattendance spa

        INNER JOIN schools_periodsession ps
            ON ps.id = spa.period_session_id

        INNER JOIN students_studentenrollment se
            ON se.id = spa.enrollment_id

        INNER JOIN schools_timetableslot ts
            ON ts.id = ps.timetable_slot_id

        INNER JOIN schools_academicclass ac
            ON ac.id = ts.academic_class_id

        INNER JOIN schools_grade g
            ON g.id = ac.grade_id

        INNER JOIN schools_section sec
            ON sec.id = ac.section_id

        WHERE

            ps.actual_teacher_id = :staff_id

        AND

            se.academic_year_id = :academic_year_id

        AND

            ps.date BETWEEN :start_date
                        AND :end_date
        """

        params = {

            "staff_id":
                context.staff_id,

            "academic_year_id":
                context.academic_year_id,

            "start_date":
                parsed_intent.start_date,

            "end_date":
                parsed_intent.end_date
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

        result = await self.db.execute(
            text(query),
            params
        )

        row = result.mappings().first()

        if not row:

            return {

                "module": "attendance",

                "attendance_percentage": 0,

                "present_periods": 0,

                "absent_periods": 0,

                "late_periods": 0,

                "total_periods": 0
            }

        total = row["total_periods"] or 0

        present = row["present_periods"] or 0

        absent = row["absent_periods"] or 0

        late = row["late_periods"] or 0

        attendance_percentage = 0

        if total:

            attendance_percentage = round(
                (
                    present
                    + late
                )
                / total
                * 100,
                2
            )

        return {

            "module": "attendance",

            "attendance_percentage":
                attendance_percentage,

            "present_periods":
                present,

            "absent_periods":
                absent,

            "late_periods":
                late,

            "total_periods":
                total
        }
    
    async def get_attendance_trend(
        self,
        context,
        parsed_intent
    ):

        regular_query = """
        SELECT

            ps.date,

            COUNT(*) FILTER (
                WHERE spa.status = 1
            ) AS present_students,

            COUNT(*) FILTER (
                WHERE spa.status = 2
            ) AS absent_students,

            COUNT(*) FILTER (
                WHERE spa.status = 3
            ) AS late_students,

            COUNT(*) AS total_students

        FROM students_studentperiodattendance spa

        INNER JOIN schools_periodsession ps
            ON ps.id = spa.period_session_id

        INNER JOIN students_studentenrollment se
            ON se.id = spa.enrollment_id

        INNER JOIN schools_timetableslot ts
            ON ts.id = ps.timetable_slot_id

        INNER JOIN schools_academicclass ac
            ON ac.id = ts.academic_class_id

        INNER JOIN schools_grade g
            ON g.id = ac.grade_id

        INNER JOIN schools_section sec
            ON sec.id = ac.section_id

        WHERE

            ps.actual_teacher_id = :staff_id

        AND

            se.academic_year_id = :academic_year_id

        AND

            ps.date BETWEEN :start_date
                        AND :end_date
        """

        params = {

            "staff_id": context.staff_id,
            "academic_year_id": context.academic_year_id,
            "start_date": parsed_intent.start_date,
            "end_date": parsed_intent.end_date
        }

        if parsed_intent.grade:

            regular_query += """
            AND g.name = :grade
            """

            params["grade"] = parsed_intent.grade

        if parsed_intent.section:

            regular_query += """
            AND sec.name = :section
            """

            params["section"] = parsed_intent.section

        regular_query += """

        GROUP BY

            ps.date

        ORDER BY

            ps.date
        """

        enrichment_query = """
        SELECT

            es.session_date AS date,

            COUNT(*) FILTER (
                WHERE ea.status = 1
            ) AS present_students,

            COUNT(*) FILTER (
                WHERE ea.status = 2
            ) AS absent_students,

            COUNT(*) FILTER (
                WHERE ea.status = 3
            ) AS late_students,

            COUNT(*) AS total_students

        FROM students_enrichmentattendance ea

        INNER JOIN schools_enrichmentsession es
            ON es.id = ea.session_id

        INNER JOIN schools_enrichmentoffering eo
            ON eo.id = es.enrichment_offering_id

        WHERE

            eo.teacher_id = :staff_id

        AND

            eo.academic_year_id = :academic_year_id

        AND

            es.session_date BETWEEN :start_date
                            AND :end_date

        GROUP BY

            es.session_date
        """

        regular = await self.db.execute(
            text(regular_query),
            params
        )

        enrichment = await self.db.execute(
            text(enrichment_query),
            params
        )

        trend = {}

        for row in regular.mappings():

            d = row["date"]

            trend[d] = {

                "date": d,

                "present_students": row["present_students"] or 0,

                "absent_students": row["absent_students"] or 0,

                "late_students": row["late_students"] or 0,

                "total_students": row["total_students"] or 0
            }

        for row in enrichment.mappings():

            d = row["date"]

            if d not in trend:

                trend[d] = {

                    "date": d,

                    "present_students": 0,

                    "absent_students": 0,

                    "late_students": 0,

                    "total_students": 0
                }

            trend[d]["present_students"] += row["present_students"] or 0
            trend[d]["absent_students"] += row["absent_students"] or 0
            trend[d]["late_students"] += row["late_students"] or 0
            trend[d]["total_students"] += row["total_students"] or 0

        data = []

        for day in sorted(trend.keys()):

            item = trend[day]

            percentage = 0

            if item["total_students"]:

                percentage = round(
                    item["present_students"]
                    * 100
                    / item["total_students"],
                    2
                )

            item["attendance_percentage"] = percentage

            data.append(item)

        return {

            "module": "attendance",

            "days": len(data),

            "trend": data
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

            COUNT(*) AS total_periods,

            COUNT(*) FILTER (
                WHERE spa.status = 1
            ) AS present_periods,

            COUNT(*) FILTER (
                WHERE spa.status = 2
            ) AS absent_periods,

            COUNT(*) FILTER (
                WHERE spa.status = 3
            ) AS late_periods

        FROM students_studentperiodattendance spa

        INNER JOIN schools_periodsession ps
            ON ps.id = spa.period_session_id

        INNER JOIN students_studentenrollment se
            ON se.id = spa.enrollment_id

        INNER JOIN students_student s
            ON s.id = se.student_id

        INNER JOIN schools_timetableslot ts
            ON ts.id = ps.timetable_slot_id

        INNER JOIN schools_academicclass ac
            ON ac.id = ts.academic_class_id

        INNER JOIN schools_grade g
            ON g.id = ac.grade_id

        INNER JOIN schools_section sec
            ON sec.id = ac.section_id

        WHERE

            ps.actual_teacher_id = :staff_id

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

            AND ps.date >= :start_date
            """

            params["start_date"] = (
                parsed_intent.start_date
            )

        if parsed_intent.end_date:

            query += """

            AND ps.date <= :end_date
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

            total = row.pop(
                "total_periods"
            ) or 0

            present = row.pop(
                "present_periods"
            ) or 0

            absent = row.pop(
                "absent_periods"
            ) or 0

            late = row.pop(
                "late_periods"
            ) or 0

            attendance_percentage = 0

            if total:

                attendance_percentage = round(

                    (
                        present + late
                    )
                    * 100
                    / total,

                    2
                )

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

            row["attendance_percentage"] = (
                attendance_percentage
            )

            row["present_periods"] = (
                present
            )

            row["absent_periods"] = (
                absent
            )

            row["late_periods"] = (
                late
            )

            students.append(
                row
            )

        return students
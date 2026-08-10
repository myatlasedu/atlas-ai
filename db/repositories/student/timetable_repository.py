from datetime import date

from sqlalchemy import text

from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")


class TimetableRepository:

    def __init__(
        self,
        db,
    ):
        self.db = db

    async def get_structure_of_day(
        self,
        enrollment_id: int,
        target_date: date,
    ):

        weekday = target_date.isoweekday()

        try:

            enrollment = await self._get_enrollment(
                enrollment_id=enrollment_id,
            )

        except ValueError:

            return {
                "date": target_date,
                "weekday": weekday,
                "lesson_count": 0,
                "enrichment_count": 0,
                "activity_count": 0,
                "break_count": 0,
                "has_teaching": False,
                "entries": [],
            }

        lessons = await self._get_lessons(
            enrollment_id=enrollment_id,
            academic_class_id=enrollment["academic_class_id"],
            weekday=weekday,
        )

        enrichments = await self._get_enrichments(
            enrollment_id=enrollment_id,
            weekday=weekday,
        )

        activities = await self._get_activities(
            academic_class_id=enrollment["academic_class_id"],
            weekday=weekday,
        )

        breaks = await self._get_breaks(
            schedule_structure_id=enrollment["schedule_structure_id"],
            weekday=weekday,
        )

        entries = self._merge_entries(
            lessons=lessons,
            enrichments=enrichments,
            activities=activities,
            breaks=breaks,
        )

        has_teaching = any(

            entry["type"] in (
                "academic",
                "enrichment",
                "activity",
            )

            for entry in entries
        )

        return {

            "date": target_date,

            "weekday": weekday,

            "lesson_count": len(lessons),

            "enrichment_count": len(enrichments),

            "activity_count": len(activities),

            "break_count": len(breaks),

            "has_teaching": has_teaching,

            "entries": (
                entries
                if has_teaching
                else []
            ),
        }

    async def _get_enrollment(
        self,
        enrollment_id: int,
    ):

        query = text(
            """
            SELECT

                se.id,

                se.academic_class_id,

                ac.schedule_structure_id

            FROM students_studentenrollment se

            INNER JOIN schools_academicclass ac

                ON ac.id = se.academic_class_id

            WHERE

                se.id = :enrollment_id

                AND se.is_active = TRUE
            """
        )

        result = await self.db.execute(
            query,
            {
                "enrollment_id": enrollment_id,
            },
        )

        row = result.mappings().first()

        if row is None:

            raise ValueError(
                "Active enrollment not found."
            )

        return row

    async def _get_breaks(
        self,
        schedule_structure_id: int,
        weekday: int,
    ):

        query = text(
            """
            SELECT

                sp.id,

                sp.name,

                sp."order",

                sp.start_time,

                sp.end_time,

                sp.is_break,

                sp.is_lunch

            FROM schools_structureperiod sp

            WHERE

                sp.structure_id = :schedule_structure_id

                AND (
                    sp.is_break = TRUE
                    OR
                    sp.is_lunch = TRUE
                )

            ORDER BY

                sp."order"
            """
        )

        result = await self.db.execute(
            query,
            {
                "schedule_structure_id": schedule_structure_id,
            },
        )

        breaks = []

        for row in result.mappings():

            breaks.append(
                {

                    "type": "break",

                    "assignment_id": None,

                    "weekday": weekday,

                    "period_id": row["id"],

                    "period_number": row["order"],

                    "period_name": row["name"],

                    "subject_offering_id": None,

                    "subject_name": row["name"],

                    "enrichment_offering_id": None,

                    "enrichment_name": None,

                    "category": None,

                    "teacher_id": None,

                    "teacher_name": None,

                    "start_time": row["start_time"],

                    "end_time": row["end_time"],

                    "combination_group": None,

                    "room_number": None,

                    "is_assessment": False,

                    "is_break": row["is_break"],

                    "is_lunch": row["is_lunch"],
                }
            )

        return breaks

    async def _get_lessons(
        self,
        enrollment_id: int,
        academic_class_id: int,
        weekday: int,
    ):

        query = text(
            """
            SELECT

                ta.id                           AS assignment_id,

                tsp.id                          AS period_id,

                tsp.name                        AS period_name,

                tsp."order"                     AS period_order,

                tsp.start_time,

                tsp.end_time,

                tsp.is_break,

                tsp.is_lunch,

                so.id                           AS subject_offering_id,

                s.name                          AS subject_name,

                st.id                           AS teacher_id,

                st.first_name,

                st.last_name,

                ta.room_number,

                ta.combination_group,

                ta.is_assessment

            FROM students_studentsubjectenrollment sse

            INNER JOIN schools_subjectoffering so

                ON so.id = sse.subject_offering_id

            INNER JOIN schools_timetableassignment ta

                ON ta.subject_offering_id = so.id

            INNER JOIN schools_timetableslot ts

                ON ts.id = ta.slot_id

            INNER JOIN schools_structureperiod tsp

                ON tsp.id = ts.period_id

            INNER JOIN schools_subjectversion sv

                ON sv.id = so.subject_version_id

            INNER JOIN schools_subject s

                ON s.id = sv.subject_id

            LEFT JOIN staff_staff st

                ON st.id = ta.teacher_id

            WHERE

                sse.enrollment_id = :enrollment_id

                AND ts.academic_class_id = :academic_class_id

                AND ts.weekday = :weekday

                AND ts.is_active = TRUE

                AND so.is_active = TRUE

            ORDER BY

                tsp."order"
            """
        )

        result = await self.db.execute(
            query,
            {
                "enrollment_id": enrollment_id,
                "academic_class_id": academic_class_id,
                "weekday": weekday,
            },
        )

        lessons = []

        for row in result.mappings():

            teacher = " ".join(
                filter(
                    None,
                    [
                        row["first_name"],
                        row["last_name"],
                    ],
                )
            )

            lessons.append(
                {
                    "type": (
                        "break"
                        if (
                            row["is_break"]
                            or
                            row["is_lunch"]
                        )
                        else
                        "academic"
                    ),

                    "assignment_id": row["assignment_id"],

                    "period_id": row["period_id"],

                    "period_number": row["period_order"],

                    "period_name": row["period_name"],

                    "subject_offering_id": row["subject_offering_id"],

                    "subject_name": row["subject_name"],

                    "teacher_id": row["teacher_id"],

                    "teacher_name": teacher or None,

                    "start_time": row["start_time"],

                    "end_time": row["end_time"],

                    "combination_group": row["combination_group"],

                    "room_number": row["room_number"],

                    "is_assessment": row["is_assessment"],

                    "is_break": row["is_break"],

                    "is_lunch": row["is_lunch"],
                }
            )

        return lessons

    async def _get_enrichments(
        self,
        enrollment_id: int,
        weekday: int,
    ):

        query = text(
            """
            SELECT

                ee.id                         AS enrollment_id,

                eo.id                         AS enrichment_offering_id,

                e.name                        AS enrichment_name,

                e.category,

                es.name                       AS slot_name,

                es.start_time,

                es.end_time,

                st.id                         AS teacher_id,

                st.first_name,

                st.last_name

            FROM schools_enrichmentenrollment ee

            INNER JOIN schools_enrichmentoffering eo

                ON eo.id = ee.enrichment_offering_id

            INNER JOIN schools_enrichmentslot es

                ON es.id = eo.slot_id

            INNER JOIN schools_enrichment e

                ON e.id = eo.enrichment_id

            LEFT JOIN staff_staff st

                ON st.id = eo.teacher_id

            WHERE

                ee.enrollment_id = :enrollment_id

                AND ee.is_active = TRUE

                AND eo.is_active = TRUE

                AND es.is_active = TRUE

                AND es.weekday = :weekday

            ORDER BY

                es.start_time
            """
        )

        result = await self.db.execute(
            query,
            {
                "enrollment_id": enrollment_id,
                "weekday": weekday,
            },
        )

        enrichments = []

        for row in result.mappings():

            teacher = " ".join(
                filter(
                    None,
                    [
                        row["first_name"],
                        row["last_name"],
                    ]
                )
            )

            enrichments.append(
                {

                    "type": "enrichment",

                    "enrichment_offering_id":
                        row["enrichment_offering_id"],

                    "enrichment_name":
                        row["enrichment_name"],

                    "category":
                        row["category"],

                    "period_name":
                        row["slot_name"],

                    "teacher_id":
                        row["teacher_id"],

                    "teacher_name":
                        teacher or None,

                    "start_time":
                        row["start_time"],

                    "end_time":
                        row["end_time"],

                    "combination_group":
                        None,

                    "room_number":
                        None,

                    "is_assessment":
                        False,
                }
            )

        return enrichments
    
    async def _get_activities(
        self,
        academic_class_id: int,
        weekday: int,
    ):

        query = text(
            """
            SELECT

                ta.id                     AS timetable_activity_id,

                a.id                      AS activity_id,

                a.name                    AS activity_name,

                ta.start_time,

                ta.end_time,

                ta.room_number,

                st.id                     AS teacher_id,

                st.first_name,

                st.last_name

            FROM schools_timetableactivity ta

            INNER JOIN schools_activity a

                ON a.id = ta.activity_id

            LEFT JOIN staff_staff st

                ON st.id = ta.teacher_id

            WHERE

                ta.academic_class_id = :academic_class_id

                AND ta.weekday = :weekday

                AND ta.is_active = TRUE

            ORDER BY

                ta.start_time
            """
        )

        result = await self.db.execute(
            query,
            {
                "academic_class_id": academic_class_id,
                "weekday": weekday,
            },
        )

        activities = []

        for row in result.mappings():

            teacher = " ".join(
                filter(
                    None,
                    [
                        row["first_name"],
                        row["last_name"],
                    ]
                )
            )

            activities.append(
                {

                    "type": "activity",

                    "assignment_id": None,

                    "weekday": weekday,

                    "period_id": None,

                    "period_number": None,

                    "period_name": row["activity_name"],

                    "subject_offering_id": None,

                    "subject_name": row["activity_name"],

                    "enrichment_offering_id": None,

                    "enrichment_name": None,

                    "category": None,

                    "activity_id": row["activity_id"],

                    "activity_name": row["activity_name"],

                    "teacher_id": row["teacher_id"],

                    "teacher_name": teacher or None,

                    "start_time": row["start_time"],

                    "end_time": row["end_time"],

                    "combination_group": None,

                    "room_number": row["room_number"],

                    "is_assessment": False,

                    "is_break": False,

                    "is_lunch": False,
                }
            )

        return activities
    
    def _merge_entries(
        self,
        lessons,
        enrichments,
        activities,
        breaks,
    ):

        entries = [

            *lessons,

            *enrichments,

            *activities,

            *breaks,
        ]

        entries.sort(

            key=lambda item: (

                item["start_time"],

                item["end_time"],
            )
        )

        return entries
    
    def get_current_entry(
        self,
        entries,
        now_time,
    ):

        for entry in entries:

            if (
                entry["start_time"]
                <= now_time
                <
                entry["end_time"]
            ):

                return entry

        return None
    
    def get_next_entry(
        self,
        entries,
        now_time,
    ):

        for entry in entries:

            if entry["start_time"] > now_time:

                return entry

        return None
    
    def build_llm_payload(
        self,
        structure,
    ):

        if not structure["has_teaching"]:

            return {

                "date": structure["date"],

                "weekday": structure["weekday"],

                "lesson_count": 0,

                "enrichment_count": 0,

                "activity_count": 0,

                "break_count": 0,

                "has_teaching": False,

                "current_entry": None,

                "next_entry": None,

                "structure_of_day": [],
            }
        
        current_datetime = datetime.now(
            IST
        )

        current_entry = None
        next_entry = None

        if structure["date"] == current_datetime.date():

            current_entry = self.get_current_entry(
                structure["entries"],
                current_datetime.time(),
            )

            next_entry = self.get_next_entry(
                structure["entries"],
                current_datetime.time(),
            )

        return {

            "date": structure["date"],

            "weekday": structure["weekday"],

            "lesson_count":
                structure["lesson_count"],

            "enrichment_count":
                structure["enrichment_count"],

            "activity_count":
                structure["activity_count"],

            "break_count":
                structure["break_count"],

            "current_entry":
                current_entry,

            "next_entry":
                next_entry,

            "structure_of_day":
                structure["entries"],
        }
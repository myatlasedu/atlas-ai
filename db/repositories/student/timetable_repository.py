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
        academic_class_id: int,
        target_date: date,
    ):

        weekday = target_date.isoweekday()

        lessons = await self._get_lessons(
            academic_class_id=academic_class_id,
            weekday=weekday,
        )

        activities = await self._get_activities(
            academic_class_id=academic_class_id,
            weekday=weekday,
        )

        entries = self._merge_entries(
            lessons,
            activities,
        )

        return {
            "date": target_date,
            "weekday": weekday,
            "lesson_count": len(lessons),
            "activity_count": len(activities),
            "entries": entries,
        }

    async def _get_lessons(
        self,
        academic_class_id: int,
        weekday: int,
    ):

        query = text(
            """
            SELECT

                tsp.id                     AS period_id,
                tsp.name                   AS period_name,
                tsp."order"                AS period_order,
                tsp.start_time,
                tsp.end_time,
                tsp.is_break,
                tsp.is_lunch,

                s.name                     AS subject,

                sv.name                    AS subject_version,

                ta.room_number,

                st.first_name,
                st.last_name

            FROM schools_timetableslot ts

            INNER JOIN schools_structureperiod tsp

                ON tsp.id = ts.period_id

            LEFT JOIN schools_timetableassignment ta

                ON ta.slot_id = ts.id

            LEFT JOIN schools_subjectoffering so

                ON so.id = ta.subject_offering_id

            LEFT JOIN schools_subjectversion sv

                ON sv.id = so.subject_version_id

            LEFT JOIN schools_subject s

                ON s.id = sv.subject_id

            LEFT JOIN staff_staff st

                ON st.id = ta.teacher_id

            WHERE

                ts.academic_class_id = :academic_class_id

                AND ts.weekday = :weekday

                AND ts.is_active = TRUE

            ORDER BY

                tsp."order"
            """
        )

        result = await self.db.execute(
            query,
            {
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
                    "type": "lesson",

                    "period_id": row["period_id"],

                    "period_name": row["period_name"],

                    "period_order": row["period_order"],

                    "start_time": (
                        row.start_time.strftime("%H:%M:%S")
                        if row.start_time
                        else None
                    ),
                    "end_time": (
                        row.end_time.strftime("%H:%M:%S")
                        if row.end_time
                        else None
                    ),

                    "subject": row["subject"],

                    "subject_version": row["subject_version"],

                    "teacher": teacher or None,

                    "room_number": row["room_number"],

                    "is_break": row["is_break"],

                    "is_lunch": row["is_lunch"],
                }
            )

        return lessons
    
    async def _get_activities(
        self,
        academic_class_id: int,
        weekday: int,
    ):

        query = text(
            """
            SELECT

                a.name AS activity_name,

                ta.start_time,

                ta.end_time,

                ta.room_number,

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
                    ],
                )
            )

            activities.append(
                {
                    "type": "activity",
                    "name": row["activity_name"],
                    "start_time": row["start_time"],
                    "end_time": row["end_time"],
                    "teacher": teacher or None,
                    "room_number": row["room_number"],
                }
            )

        return activities
    
    def _merge_entries(
        self,
        lessons,
        activities,
    ):

        entries = []

        entries.extend(lessons)

        entries.extend(activities)

        entries.sort(
            key=lambda x: (
                x["start_time"],
                x["end_time"],
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

        current_datetime = datetime.now(IST)

        if structure["date"] == current_datetime.date():

            current_entry = self.get_current_entry(
                structure["entries"],
                current_datetime.time(),
            )

            next_entry = self.get_next_entry(
                structure["entries"],
                current_datetime.time(),
            )

        else:

            current_entry = None

            next_entry = None

        return {

            "date": structure["date"],

            "weekday": structure["weekday"],

            "lesson_count": structure["lesson_count"],

            "activity_count": structure["activity_count"],

            "current_lesson": current_entry,

            "next_lesson": next_entry,

            "structure_of_the_day": structure["entries"],
        }
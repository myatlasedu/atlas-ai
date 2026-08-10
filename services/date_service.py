from datetime import date

from intents.mentor.enums import (
    MentorIntent
)
from utils import ist_today

class DateService:

    @staticmethod
    def validate(
        parsed_intent
    ):

        is_attendance = (
            parsed_intent.intent
            == "attendance_summary"
        )

        # 1. Fill missing attendance dates for any role
        if is_attendance:

            if not parsed_intent.start_date:

                parsed_intent.start_date = ist_today()

            if not parsed_intent.end_date:

                parsed_intent.end_date = ist_today()

        # 2. Fix reversed range (protect all intents)
        if (
            parsed_intent.start_date
            and
            parsed_intent.end_date
            and
            parsed_intent.end_date < parsed_intent.start_date
        ):

            (
                parsed_intent.start_date,
                parsed_intent.end_date,
            ) = (
                parsed_intent.end_date,
                parsed_intent.start_date,
            )

        # 3. Attendance dates cannot be in the future
        if (
            is_attendance
            and
            parsed_intent.start_date
            and
            parsed_intent.start_date > ist_today()
        ):

            parsed_intent.start_date = ist_today()

        return parsed_intent
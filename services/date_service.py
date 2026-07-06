from datetime import date

from intents.mentor.enums import (
    MentorIntent
)


class DateService:

    @staticmethod
    def validate(
        parsed_intent
    ):

        if (
            parsed_intent.start_date
            and
            parsed_intent.end_date
        ):
            return parsed_intent

        if parsed_intent.intent == MentorIntent.ATTENDANCE_SUMMARY:

            today = date.today()

            parsed_intent.start_date = today

            parsed_intent.end_date = today

        return parsed_intent
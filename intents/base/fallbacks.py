from datetime import date

from intents.student.enums import (
    StudentIntent
)


def build_fallback_student_intent():

    today = (
        date.today()
        .isoformat()
    )

    return {

        "intent":
            StudentIntent.UNKNOWN,

        "start_date":
            today,

        "end_date":
            today,

        "target_modules":
            [],

        "confidence":
            0.0
    }
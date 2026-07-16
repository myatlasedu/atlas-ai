from datetime import date

from intents.student.enums import (
    StudentIntent
)
from utils import ist_today

def build_fallback_student_intent():

    today = (
        ist_today()
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
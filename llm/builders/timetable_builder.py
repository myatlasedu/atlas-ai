def build_timetable_llm_context(
    structure: dict,
) -> dict:

    return {

        "date":
            structure.get(
                "date"
            ),

        "weekday":
            structure.get(
                "weekday"
            ),

        "lesson_count":
            structure.get(
                "lesson_count",
                0,
            ),

        "activity_count":
            structure.get(
                "activity_count",
                0,
            ),

        "current_lesson":
            structure.get(
                "current_lesson"
            ),

        "next_lesson":
            structure.get(
                "next_lesson"
            ),

        "structure_of_the_day":
            structure.get(
                "entries",
                []
            ),
    }
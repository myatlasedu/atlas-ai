from intents.student.enums import (
    StudentIntent
)

from intents.student.parser import (
    parse_student_intent
)

# from intents.parent.parser import (
#     parse_parent_intent
# )

from intents.mentor.parser import (
    parse_mentor_intent
)


async def parse_intent(
    query: str,
    role: str,
    enrollment_id: int | None = None,
    forced_intent: str | None = None,
    raw_query: str | None = None,
):

    #
    # `query` is the standalone query. For a context-resolved
    # follow-up it is the rewrite, and `raw_query` is what the
    # user actually typed.
    #
    # `forced_intent` skips classification when the conversation
    # already established the intent.
    #

    role = (
        role
        .strip()
        .lower()
    )

    if role == "student":

        return await parse_student_intent(
            query=query,
            enrollment_id=enrollment_id,
            forced_intent=_as_student_intent(
                forced_intent
            ),
            raw_query=raw_query,
        )

    
    # if role == "parent":

    #     return await parse_parent_intent(
    #         query=query
    #     )

    if role == "mentor":

        return await parse_mentor_intent(
            query=query
        )

    raise ValueError(
        f"Unsupported role: {role}"
    )


def _as_student_intent(
    value,
) -> StudentIntent | None:

    if not value:

        return None

    if isinstance(
        value,
        StudentIntent,
    ):

        return value

    try:

        return StudentIntent(
            str(value).strip().lower()
        )

    except ValueError:

        return None

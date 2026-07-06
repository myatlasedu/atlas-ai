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
    role: str
):

    role = (
        role
        .strip()
        .lower()
    )

    if role == "student":

        return await parse_student_intent(
            query=query
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
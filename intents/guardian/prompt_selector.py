from intents.guardian.classifier import (
    classify_guardian_intent
)

from intents.guardian.enums import (
    GuardianIntent
)

from intents.guardian.prompts import (
    get_guardian_intent_prompt
)


async def build_prompt_for_query(
    query: str
):

    result = await classify_guardian_intent(
        query
    )

    intent = GuardianIntent(
        result["intent"]
    )

    return get_guardian_intent_prompt(
        intent
    )
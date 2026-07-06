import logging

from llm.client import (
    chat_completion
)

from intents.base.parser import (
    parse_llm_json
)

from intents.guardian.enums import (
    GuardianIntent
)

from intents.guardian.classifier_prompt import (
    CLASSIFIER_PROMPT
)

logger = logging.getLogger(__name__)


async def classify_guardian_intent(
    query: str
) -> GuardianIntent:

    response = await chat_completion(
        messages=[
            {
                "role": "system",
                "content": CLASSIFIER_PROMPT
            },
            {
                "role": "user",
                "content": query
            }
        ]
    )

    parsed = parse_llm_json(
        response["message"]["content"]
    )

    intent = parsed.get(
        "intent",
        "unknown"
    )

    logger.info(
        "Guardian intent classified: %s",
        intent
    )

    try:

        return GuardianIntent(
            intent
        )

    except Exception:

        logger.warning(
            "Unknown guardian intent '%s'",
            intent
        )

        return GuardianIntent.UNKNOWN
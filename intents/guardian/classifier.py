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
    query: str,
    prior_context: str | None = None,
) -> GuardianIntent:

    user_content = query

    if prior_context:

        user_content = (
            f"PRIOR CONVERSATION\n\n"
            f"{prior_context}\n\n"
            f"QUESTION\n\n{query}\n\n"
            "Use the prior conversation only to "
            "resolve references (subjects, dates, "
            "pronouns)."
        )

    response = await chat_completion(
        messages=[
            {
                "role": "system",
                "content": CLASSIFIER_PROMPT
            },
            {
                "role": "user",
                "content": user_content
            }
        ],
        expect_json=True
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
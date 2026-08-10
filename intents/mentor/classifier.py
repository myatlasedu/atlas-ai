import logging

from llm.client import chat_completion

from intents.base.parser import parse_llm_json

from intents.mentor.enums import MentorIntent

from intents.mentor.classifier_prompt import (
    CLASSIFIER_PROMPT
)

logger = logging.getLogger(__name__)


async def classify_mentor_intent(
    query: str,
    prior_context: str | None = None,
) -> MentorIntent:

    user_content = query

    if prior_context:

        user_content = (
            f"PRIOR CONVERSATION\n\n"
            f"{prior_context}\n\n"
            f"QUESTION\n\n{query}\n\n"
            "Use the prior conversation only to "
            "resolve references (subjects, classes, "
            "dates)."
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

    content = response["message"]["content"]

    logger.info(
        "MENTOR CLASSIFIER: %s",
        content
    )

    parsed = parse_llm_json(
        content
    )

    try:

        return MentorIntent(
            parsed["intent"]
        )

    except Exception:

        return MentorIntent.UNKNOWN
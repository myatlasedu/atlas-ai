import logging

from llm.client import (
    chat_completion
)

from intents.base.parser import (
    parse_llm_json
)

from intents.student.enums import (
    StudentIntent
)

from intents.student.classifier_prompt import (
    CLASSIFIER_PROMPT
)

logger = logging.getLogger(__name__)


async def classify_student_intent(
    query: str
) -> StudentIntent:

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
        "Student intent classified: %s",
        intent
    )

    try:

        return StudentIntent(
            intent
        )

    except Exception:

        return StudentIntent.UNKNOWN
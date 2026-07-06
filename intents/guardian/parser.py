import logging

from llm.client import (
    chat_completion
)

from intents.base.parser import (
    parse_llm_json
)

from intents.guardian.classifier import (
    classify_guardian_intent
)

from intents.guardian.enums import (
    GuardianIntent
)

from intents.guardian.prompts import (
    get_guardian_intent_prompt
)

from intents.guardian.schemas import (
    ParsedGuardianIntent
)

from utils import (
    resolve_dates
)

logger = logging.getLogger(__name__)


VALID_INTENTS = {

    item.value

    for item

    in GuardianIntent
}


async def parse_guardian_intent(
    query: str
) -> ParsedGuardianIntent:

    try:

        classified_intent = (
            await classify_guardian_intent(
                query
            )
        )

        logger.info(
            "Guardian classified intent: %s",
            classified_intent.value
        )

        response = await chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": get_guardian_intent_prompt(
                        classified_intent
                    )
                },
                {
                    "role": "user",
                    "content": query
                }
            ]
        )

        content = (
            response["message"]["content"]
        )

        logger.info(
            "GUARDIAN RAW RESPONSE >>> %r",
            content
        )

        parsed = parse_llm_json(
            content
        )

        logger.info(
            "Guardian parsed JSON >>> %s",
            parsed
        )

        intent = (
            str(
                parsed.get(
                    "intent",
                    classified_intent.value
                )
            )
            .strip()
            .lower()
        )

        if intent not in VALID_INTENTS:

            logger.warning(
                "Unknown guardian intent '%s'. Falling back to classifier intent.",
                intent
            )

            intent = (
                classified_intent.value
            )

        parsed["intent"] = intent

        parsed = resolve_dates(
            parsed
        )

        parsed.setdefault(
            "target_modules",
            []
        )

        parsed.setdefault(
            "confidence",
            0.95
        )

        parsed["original_query"] = query

        return ParsedGuardianIntent(
            **parsed
        )

    except Exception:

        logger.exception(
            "Guardian intent parsing failed."
        )

        return ParsedGuardianIntent(

            intent=GuardianIntent.UNKNOWN.value,

            target_modules=[],

            confidence=0.0,

            original_query=query
        )
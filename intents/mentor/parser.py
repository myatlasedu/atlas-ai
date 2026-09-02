import logging

from llm.client import (
    chat_completion
)

from intents.base.parser import (
    parse_llm_json
)

from intents.mentor.schemas import (
    ParsedMentorIntent
)

from intents.mentor.prompts import (
    get_mentor_intent_prompt
)

from utils import (
    resolve_dates
)

from intents.mentor.classifier import classify_mentor_intent

logger = logging.getLogger(__name__)


async def parse_mentor_intent(
    query: str
) -> ParsedMentorIntent:
    
    intent = await classify_mentor_intent(
        query
    )

    response = await chat_completion(
        messages=[
            {
                "role": "system",
                "content": get_mentor_intent_prompt(
                    intent
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
        "MENTOR RAW RESPONSE: %s",
        content
    )

    parsed = parse_llm_json(
        content
    )

    parsed["original_query"] = query

    parsed = resolve_dates(
        parsed
    )

    parsed[
        "original_query"
    ] = query

    return ParsedMentorIntent(
        **parsed
    )
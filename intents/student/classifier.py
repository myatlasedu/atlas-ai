import logging

from llm.client import (
    chat_completion,
)

from intents.base.parser import (
    parse_llm_json,
)

from intents.common.conversation_context import (
    IntentClassification,
    build_classifier_messages,
    resolve_context_turn,
    resolve_followup_query,
)

from intents.student.enums import (
    StudentIntent,
)

from intents.student.classifier_prompt import (
    CLASSIFIER_PROMPT,
)

from schemas.conversation import (
    ConversationTurn,
)

logger = logging.getLogger(__name__)


async def classify_student_intent(
    query: str,
    turns: list[ConversationTurn] | None = None,
) -> IntentClassification:

    messages=build_classifier_messages(
        base_prompt=CLASSIFIER_PROMPT,
        query=query,
        turns=turns,
    )


    response = await chat_completion(
        messages=messages,
        expect_json=True,
        thinking=False
    )

    logger.debug(
        "Classifier response: %s",
        response,
    )
    print("\n====Chat Completion complete for intent classification===")
    parsed = parse_llm_json(
        response["message"]["content"]
    )
    print("\n====Parsed LLM JSON pass===")
    intent = (
        str(
            parsed.get(
                "intent",
                "unknown",
            )
        )
        .strip()
        .lower()
    )

    print("\n====Parsed (LLM Response) contain all thing====")
    print(parsed)

    context_turn = resolve_context_turn(
        turns=turns,
        context_turn=parsed.get(
            "context_turn"
        ),
    )

    is_follow_up = bool(
        turns
        and
        parsed.get(
            "is_follow_up",
            False,
        )
    )

    resolved_query = resolve_followup_query(
        query=query,
        resolved_query=parsed.get(
            "resolved_query"
        ),
        is_follow_up=is_follow_up,
        context_turn=context_turn,
    )

    print("=====Follow-up / resolved query=====")
    print(is_follow_up, "|", resolved_query)

    logger.info(
        "Student intent classified: %s "
        "(follow-up: %s, context turn: %s, resolved: %r)",
        intent,
        is_follow_up,
        context_turn.turn_id
        if context_turn
        else None,
        resolved_query,
    )

    try:

        classified = StudentIntent(
            intent
        )

    except ValueError:

        logger.warning(
            "Invalid student intent returned by classifier: %s",
            intent,
        )

        return IntentClassification(
            StudentIntent.UNKNOWN,
            resolved_query=resolved_query,
            is_follow_up=is_follow_up,
        )

    return IntentClassification(
        classified,
        context_turn,
        resolved_query=resolved_query,
        is_follow_up=is_follow_up,
    )

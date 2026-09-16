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

from intents.common.conversation_context import (
    IntentClassification,
    align_intent_with_context_turn,
    build_classifier_messages,
    resolve_context_turn,
    resolve_followup_query,
)

from schemas.conversation import (
    ConversationTurn
)

logger = logging.getLogger(__name__)


async def classify_guardian_intent(
    query: str,
    turns: list[ConversationTurn] | None = None,
) -> IntentClassification:

    response = await chat_completion(
        messages=build_classifier_messages(
            base_prompt=CLASSIFIER_PROMPT,
            query=query,
            turns=turns,
        ),
        expect_json=True,
    )

    parsed = parse_llm_json(
        response["message"]["content"]
    )

    intent = parsed.get(
        "intent",
        "unknown"
    )

    is_follow_up = bool(
        turns
        and
        parsed.get(
            "is_follow_up",
            False,
        )
    )

    context_turn = resolve_context_turn(
        turns=turns,
        context_turn=parsed.get(
            "context_turn"
        ),
        query=(
            query
            if is_follow_up
            else None
        ),
    )

    intent = align_intent_with_context_turn(
        intent=intent,
        context_turn=context_turn,
        is_follow_up=is_follow_up,
        query=query,
    )

    resolved_query = resolve_followup_query(
        query=query,
        resolved_query=parsed.get(
            "resolved_query"
        ),
        is_follow_up=is_follow_up,
        context_turn=context_turn,
    )

    logger.info(
        "Guardian intent classified: %s "
        "(follow-up: %s, context turn: %s, resolved: %r)",
        intent,
        is_follow_up,
        context_turn.turn_id
        if context_turn
        else None,
        resolved_query,
    )

    try:

        classified = GuardianIntent(
            intent
        )

    except Exception:

        logger.warning(
            "Unknown guardian intent '%s'",
            intent
        )

        return IntentClassification(
            GuardianIntent.UNKNOWN,
            resolved_query=resolved_query,
            is_follow_up=is_follow_up,
        )

    return IntentClassification(
        classified,
        context_turn,
        resolved_query=resolved_query,
        is_follow_up=is_follow_up,
    )
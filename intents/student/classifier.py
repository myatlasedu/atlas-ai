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
    build_context_resolution,
    followed_wrong_turn,
    is_conversation_recall_query,
    is_meta_intent,
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

    parsed = parse_llm_json(
        response["message"]["content"]
    )

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

    print("\n====Parsed (LLM Response) in student classifier====")
    print(parsed)

    if intent == "unknown" and is_conversation_recall_query(query):
        logger.info(
            "Overriding unknown to conversation_recall for query: %r",
            query,
        )
        intent = StudentIntent.CONVERSATION_RECALL.value

    is_follow_up = bool(
        turns
        and
        parsed.get(
            "is_follow_up",
            False,
        )
        and
        not is_meta_intent(
            intent
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

    # A bare filter continues the most recent turn. If the classifier
    # answered from an older one, keep neither its rewrite nor its intent.

    wrong_turn = is_follow_up and followed_wrong_turn(
        query=query,
        raw_context_turn=parsed.get(
            "context_turn"
        ),
        context_turn=context_turn,
        turns=turns,
    )

    if wrong_turn:

        logger.info(
            "Follow-up %r answered from turn %r; continuing turn %s (%s) instead.",
            query,
            parsed.get("context_turn"),
            context_turn.turn_id,
            context_turn.predicted_intent,
        )

        intent = context_turn.predicted_intent

    resolved_query = resolve_followup_query(
        query=query,
        resolved_query=parsed.get(
            "resolved_query"
        ),
        is_follow_up=is_follow_up,
        context_turn=context_turn,
        rebuild=wrong_turn,
    )
    print("\n====Resolved Query in student classifier====")
    print(resolved_query)

    context_resolution = build_context_resolution(
        is_follow_up=is_follow_up,
        resolved_query=resolved_query,
        intent=intent,
        context_turn=context_turn,
    )

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
            context_resolution=context_resolution,
        )

    return IntentClassification(
        classified,
        context_turn,
        resolved_query=resolved_query,
        is_follow_up=is_follow_up,
        context_resolution=context_resolution,
    )

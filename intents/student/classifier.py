import logging

from llm.client import (
    chat_completion,
)

from starlette.concurrency import run_in_threadpool
# from intents.base.parser import (
#     parse_llm_json,
# )

from services.intent_classifier import MiniLMIntentClassifier

from intents.student.enums import (
    StudentIntent,
)

# from intents.student.classifier_prompt import (
#     CLASSIFIER_PROMPT,
# )

logger = logging.getLogger(__name__)

#Old LLM APPROACH REMOVE LATER
# async def classify_student_intent(
#     query: str,
# ) -> StudentIntent:

#     response = await chat_completion(
#         messages=[
#             {
#                 "role": "system",
#                 "content": CLASSIFIER_PROMPT,
#             },
#             {
#                 "role": "user",
#                 "content": query,
#             },
#         ],
#         thinking=False
#     )

#     logger.debug(
#         "Classifier response: %s",
#         response,
#     )

#     parsed = parse_llm_json(
#         response["message"]["content"]
#     )

#     intent = (
#         str(
#             parsed.get(
#                 "intent",
#                 "unknown",
#             )
#         )
#         .strip()
#         .lower()
#     )

#     logger.info(
#         "Student intent classified: %s",
#         intent,
#     )

#     try:

#         return StudentIntent(
#             intent
#         )

#     except ValueError:

#         logger.warning(
#             "Invalid student intent returned by classifier: %s",
#             intent,
#         )

#         return StudentIntent.UNKNOWN

async def classify_student_intent(
    query: str,
    classifier: MiniLMIntentClassifier,
) -> StudentIntent:

    prediction = await run_in_threadpool(
        classifier.predict,
        query,
    )

    logger.info(
        "MiniLM classification: intent=%s confidence=%.4f alternatives=%s",
        prediction.intent,
        prediction.confidence,
        prediction.alternatives,
    )

    try:
        return StudentIntent(
            prediction.intent
        )

    except ValueError:
        logger.warning(
            "MiniLM returned an unsupported intent: %s",
            prediction.intent,
        )

        return StudentIntent.UNKNOWN
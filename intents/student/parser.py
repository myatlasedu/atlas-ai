import logging

from llm.client import (
    chat_completion,
)

from intents.base.fallbacks import (
    build_fallback_student_intent,
)

from intents.base.parser import (
    parse_llm_json,
)

from intents.student.classifier import (
    classify_student_intent,
)

from intents.student.enums import (
    StudentIntent,
)

from intents.student.prompts import (
    get_student_intent_prompt,
)

from intents.student.schemas import (
    ParsedStudentIntent,
)

from utils import (
    resolve_dates,
)


logger = logging.getLogger(__name__)


def _fallback(
    query: str,
) -> ParsedStudentIntent:

    data = build_fallback_student_intent()

    data["original_query"] = query

    return ParsedStudentIntent(
        **data
    )


def _normalize_modules(
    parsed: dict,
) -> dict:

    modules = parsed.get(
        "target_modules",
        [],
    )

    if not isinstance(
        modules,
        list,
    ):
        modules = []

    parsed["target_modules"] = list(
        dict.fromkeys(
            str(module).lower().strip()
            for module in modules
            if module
        )
    )

    return parsed


def _normalize_dates(
    parsed: dict,
) -> dict:

    parsed = resolve_dates(
        parsed
    )

    for field in (
        "start_date",
        "end_date",
    ):

        value = parsed.get(
            field
        )

        if hasattr(
            value,
            "isoformat",
        ):

            parsed[field] = (
                value.isoformat()
            )

    return parsed


async def parse_student_intent(
    query: str,
) -> ParsedStudentIntent:

    try:

        # ==================================================
        # STEP 1
        # CLASSIFY INTENT
        # ==================================================

        classified_intent = (
            await classify_student_intent(
                query
            )
        )

        logger.info(
            "Classified intent: %s",
            classified_intent.value,
        )

        # ==================================================
        # STEP 2
        # PARAMETER EXTRACTION
        #
        # The classifier's intent is authoritative.
        # The second LLM must NOT re-classify the query.
        # ==================================================

        prompt = (
            get_student_intent_prompt(
                classified_intent
            )
        )

        response = await chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": prompt,
                },
                {
                    "role": "user",
                    "content": query,
                },
            ]
        )

        content = (
            response["message"]["content"]
        )

        logger.info(
            "RAW PARAMETER MODEL RESPONSE >>> %r",
            content,
        )

        parsed = parse_llm_json(
            content
        )

        logger.info(
            "Parsed parameters >>> %s",
            parsed,
        )

        # ==================================================
        # STEP 3
        # FORCE CLASSIFIER INTENT
        #
        # Never trust the second LLM's intent field.
        # ==================================================

        parsed["intent"] = (
            classified_intent.value
        )

        # ==================================================
        # STEP 4
        # DEFAULT MODULES
        # ==================================================

        parsed.setdefault(
            "target_modules",
            [],
        )

        # ==================================================
        # STEP 5
        # ORIGINAL QUERY
        # ==================================================

        parsed["original_query"] = query

        # ==================================================
        # STEP 6
        # NORMALIZE DATES
        # ==================================================

        parsed = _normalize_dates(
            parsed
        )

        # ==================================================
        # STEP 7
        # NORMALIZE MODULES
        # ==================================================

        parsed = _normalize_modules(
            parsed
        )

        # ==================================================
        # STEP 8
        # BUILD FINAL SCHEMA
        # ==================================================

        return ParsedStudentIntent(
            **parsed
        )

    except Exception:

        logger.exception(
            "Student intent parsing failed."
        )

        return _fallback(
            query
        )
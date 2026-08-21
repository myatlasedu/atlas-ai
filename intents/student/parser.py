import logging

from datetime import date
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


async def _normalize_dates(
    parsed: dict,
) -> dict:

    parsed = await resolve_dates(
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

        elif isinstance(
            value,
            str,
        ):

            #
            # Defensive: the LLM sometimes returns
            # non-ISO date strings (e.g. "28 July").
            # Never let them crash intent validation.
            #

            try:

                parsed[field] = (
                    date.fromisoformat(
                        value
                    )
                    .isoformat()
                )

            except ValueError:

                parsed[field] = None

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
            ],
            expect_json=True,
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

        # ------------------------------------------------------
        # Narrow safety net: marks FOR a specific homework /
        # assignment / worksheet must route to homework_summary,
        # never assessment_summary. Only applies when the
        # parser set asks_for_marks AND a specific topic title.
        # ------------------------------------------------------

        if (
            parsed["intent"]
            ==
            StudentIntent.ASSESSMENT_SUMMARY.value
            and
            parsed.get(
                "asks_for_marks",
                False,
            )
            and
            parsed.get(
                "topic",
                None,
            )
        ):

            logger.info(
                "Reclassifying assessment intent to homework_summary: %r",
                query,
            )

            parsed["intent"] = (
                StudentIntent.HOMEWORK_SUMMARY.value
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

        parsed = await _normalize_dates(
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
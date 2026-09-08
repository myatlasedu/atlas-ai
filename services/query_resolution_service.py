import logging
import time

from datetime import date

from intents.base.parser import (
    parse_llm_json,
)

from intents.guardian.enums import (
    GuardianIntent,
)

from intents.mentor.enums import (
    MentorIntent,
)

from intents.student.enums import (
    StudentIntent,
)

from llm.client import (
    chat_completion,
)

from llm.query_resolver_prompt import (
    build_query_resolver_messages,
)

from schemas.conversation import (
    BOOLEAN_PARAMETERS,
    CROSS_INTENT_INHERITABLE_PARAMETERS,
    Clarification,
    ContextUsage,
    ConversationTurn,
    DATE_PARAMETERS,
    LIST_PARAMETERS,
    QueryResolution,
    SAME_INTENT_INHERITABLE_PARAMETERS,
)

from services.temporal_service import (
    TemporalService,
)


logger = logging.getLogger(__name__)


ROLE_INTENT_ENUM = {

    "student": StudentIntent,

    "mentor": MentorIntent,

    "guardian": GuardianIntent,
}


#
# Intents that must never be inherited: they are one-shot
# actions, not a subject the user can keep asking about.
#

NON_INHERITABLE_INTENTS = frozenset(
    {
        "unknown",
        "action_confirmation",
        "screen_navigation",
        "personal_event_create",
        "journal_create",
    }
)


class QueryResolutionService:

    MAX_TOKENS = 700

    # ==================================================
    # PUBLIC ENTRY POINT
    # ==================================================

    @classmethod
    async def resolve(
        cls,
        *,
        query: str,
        context,
        turns: list[ConversationTurn],
    ) -> QueryResolution:

        start = time.perf_counter()

        #
        # No history means nothing to resolve against. Skipping the
        # LLM call keeps first-turn latency identical to before.
        #

        if not turns:

            return QueryResolution.passthrough(
                query,
                reason="No recent conversation to resolve against.",
            )

        try:

            resolution = await cls._resolve_with_llm(
                query=query,
                context=context,
                turns=turns,
            )

        except Exception:

            #
            # Resolution is an enhancement, never a dependency.
            # A failure degrades to the stateless pipeline.
            #

            logger.exception(
                "Query resolution failed; "
                "falling back to the raw query."
            )

            resolution = QueryResolution.passthrough(
                query,
                reason="Query resolution failed.",
            )

        resolution.latency_ms = int(
            (
                time.perf_counter()
                - start
            )
            * 1000
        )

        logger.info(
            "Query resolution: %s",
            resolution.contract(),
        )

        return resolution

    # ==================================================
    # LLM RESOLUTION
    # ==================================================

    @classmethod
    async def _resolve_with_llm(
        cls,
        *,
        query: str,
        context,
        turns: list[ConversationTurn],
    ) -> QueryResolution:

        role = (
            str(context.role)
            .strip()
            .lower()
        )

        today = TemporalService.today(
            context
        )
        print("\n=====IN query_resolution_service======")
        print("At 170")
        # print("Turns: ", turns)
        messages = build_query_resolver_messages(

            role=role,

            allowed_intents=cls._allowed_intents(
                role
            ),

            today=today.isoformat(),

            timezone_name=(
                TemporalService.timezone_name(
                    context
                )
            ),

            turns=turns,

            query=query,
        )
        print("\n=====IN query_resolution_service at 190======")
        
        response = await chat_completion(

            messages=messages,

            expect_json=True,

            max_tokens=cls.MAX_TOKENS,

            thinking=False,
        )
        print("RESPONSE after query_resolution_service at 204")
        print(response)
        raw = parse_llm_json(
            response["message"]["content"]
        )

        return cls._normalize(

            raw=raw,

            query=query,

            role=role,

            turns=turns,

            today=today,
        )

    # ==================================================
    # NORMALIZATION
    # ==================================================

    @classmethod
    def _normalize(
        cls,
        *,
        raw: dict,
        query: str,
        role: str,
        turns: list[ConversationTurn],
        today: date,
    ) -> QueryResolution:

        # ----------------------------------------------
        # Resolved query
        # ----------------------------------------------

        resolved_query = str(
            raw.get(
                "resolved_query",
                "",
            )
            or ""
        ).strip()

        if not resolved_query:

            resolved_query = query

        # ----------------------------------------------
        # Context usage
        # ----------------------------------------------

        context_used = cls._normalize_context_usage(
            raw.get("context_used"),
            turns=turns,
        )

        # ----------------------------------------------
        # Clarification
        # ----------------------------------------------

        clarification = cls._normalize_clarification(
            raw.get("clarification_required")
        )

        #
        # A clarification only means something if the resolver
        # actually consulted the conversation. Claiming the message
        # "stands on its own" AND asking what it means are
        # contradictory, and honouring the question would stall a
        # follow-up that history could have answered.
        #

        if (
            clarification.required
            and not context_used.used
        ):

            logger.info(
                "Resolver asked for clarification without using the "
                "conversation; treating the message as a follow-up."
            )

            clarification = Clarification()

            context_used = cls._recover_context_usage(
                context_used,
                turns=turns,
            )

            recovered = True

        else:

            recovered = False

        if clarification.required:

            # An ambiguous turn must not carry an intent or
            # parameters forward: the user has to answer first.

            return QueryResolution(

                resolved_query=resolved_query,

                intent=None,

                parameters={},

                context_used=context_used,

                clarification_required=clarification,

                inherited_intent=False,
            )

        # ----------------------------------------------
        # Intent
        # ----------------------------------------------

        intent = cls._normalize_intent(
            raw.get("intent"),
            role=role,
        )

        if recovered and intent is None:

            # Recovery is only useful if the intent comes with it;
            # otherwise the classifier still sees a bare fragment.

            intent = cls._normalize_intent(
                turns[0].predicted_intent,
                role=role,
            )

            logger.info(
                "Recovered intent from the previous turn: %s",
                intent,
            )

        inherited_intent = bool(
            intent
            and context_used.used
        )

        # The resolver may only inherit an intent the conversation
        # actually contains; anything else is a guess, and the
        # classifier is the component that is allowed to guess.

        known_intents = {
            cls._intent_value(turn.predicted_intent)
            for turn in turns
        }

        if (
            inherited_intent
            and intent not in known_intents
        ):

            logger.info(
                "Resolver proposed intent %r absent from history; "
                "deferring to the classifier.",
                intent,
            )

            intent = None

            inherited_intent = False

        # ----------------------------------------------
        # Parameters
        # ----------------------------------------------

        source = cls._select_source_turn(
            turns,
            intent=intent,
            context_used=context_used,
        )

        same_intent = bool(
            intent
            and intent == cls._intent_value(
                source.predicted_intent
            )
        )

        allowed = (
            SAME_INTENT_INHERITABLE_PARAMETERS
            if same_intent
            else CROSS_INTENT_INHERITABLE_PARAMETERS
        )

        extracted = cls._sanitize_parameters(
            raw.get("parameters"),
        )

        inherited = source.parameters(
            allowed
        )

        parameters = cls._merge_parameters(

            previous=inherited,

            extracted=extracted,

            context_used=context_used,
        )

        parameters = cls._apply_relative_window(

            parameters=parameters,

            query=query,

            resolved_query=resolved_query,

            today=today,
        )

        parameters = cls._validate_window(
            parameters
        )

        return QueryResolution(

            resolved_query=resolved_query,

            intent=intent,

            parameters=parameters,

            context_used=context_used,

            clarification_required=clarification,

            inherited_intent=inherited_intent,
        )

    # ==================================================
    # FIELD NORMALIZERS
    # ==================================================

    @staticmethod
    def _intent_value(
        value,
    ) -> str:

        return (
            str(
                getattr(
                    value,
                    "value",
                    value,
                )
                or ""
            )
            .strip()
            .lower()
        )

    @classmethod
    def _allowed_intents(
        cls,
        role: str,
    ) -> list[str]:

        enum = ROLE_INTENT_ENUM.get(
            role
        )

        if enum is None:

            return []

        return [
            member.value
            for member in enum
            if member.value
            not in NON_INHERITABLE_INTENTS
        ]

    @classmethod
    def _normalize_intent(
        cls,
        value,
        *,
        role: str,
    ) -> str | None:

        intent = cls._intent_value(
            value
        )

        if (
            not intent
            or intent in ("null", "none")
        ):

            return None

        if intent in NON_INHERITABLE_INTENTS:

            return None

        if intent not in cls._allowed_intents(role):

            logger.warning(
                "Resolver returned an unknown intent: %r",
                intent,
            )

            return None

        return intent

    @classmethod
    def _recover_context_usage(
        cls,
        context_used: ContextUsage,
        *,
        turns: list[ConversationTurn],
    ) -> ContextUsage:

        #
        # The resolver flagged the message as a fragment that needs
        # more detail, which is itself evidence that it depends on
        # the conversation. Attach it to the most recent turn so the
        # intent and parameters below can still be inherited.
        #

        previous = turns[0]

        return ContextUsage(

            used=True,

            turn_ids=[
                previous.turn_id
            ],

            inherited_fields=[
                "intent"
            ],

            reason=(
                "Recovered: the resolver could not resolve the "
                "fragment on its own, so it continues the previous "
                "turn."
            ),
        )

    @classmethod
    def _select_source_turn(
        cls,
        turns: list[ConversationTurn],
        *,
        intent: str | None,
        context_used: ContextUsage,
    ) -> ConversationTurn:

        #
        # The turn a follow-up actually continues.
        #
        # Usually the latest one, but a user can pick up a thread
        # they dropped ("and last week's homework?" after an
        # attendance question). Inheriting from the newest turn
        # there would hand back the wrong filters, so prefer the
        # most recent turn the resolver cited whose intent matches
        # the one being inherited.
        #

        cited = [
            turn
            for turn in turns
            if turn.turn_id in context_used.turn_ids
        ]

        if intent:

            for turn in (cited or turns):

                if cls._intent_value(
                    turn.predicted_intent
                ) == intent:

                    return turn

        if cited:

            return cited[0]

        return turns[0]

    @classmethod
    def _normalize_context_usage(
        cls,
        value,
        *,
        turns: list[ConversationTurn],
    ) -> ContextUsage:

        if not isinstance(
            value,
            dict,
        ):

            return ContextUsage()

        known_ids = {
            turn.turn_id
            for turn in turns
        }

        turn_ids = []

        for item in (
            value.get("turn_ids")
            or []
        ):

            try:

                turn_id = int(item)

            except (TypeError, ValueError):

                continue

            if turn_id in known_ids:

                turn_ids.append(
                    turn_id
                )

        inherited_fields = [
            str(field).strip()
            for field in (
                value.get("inherited_fields")
                or []
            )
            if str(field).strip()
        ]

        return ContextUsage(

            used=bool(
                value.get("used")
            ),

            turn_ids=turn_ids,

            inherited_fields=inherited_fields,

            reason=(
                str(value["reason"]).strip()
                if value.get("reason")
                else None
            ),
        )

    @staticmethod
    def _normalize_clarification(
        value,
    ) -> Clarification:

        if not isinstance(
            value,
            dict,
        ):

            return Clarification()

        question = (
            str(value.get("question") or "")
            .strip()
        )

        required = bool(
            value.get("required")
        )

        if required and not question:

            # A clarification with nothing to ask would stall the
            # conversation; proceed with the best reading instead.

            logger.warning(
                "Resolver requested clarification without a question."
            )

            return Clarification()

        return Clarification(

            required=required,

            question=(
                question
                or None
            ),

            reason=(
                str(value["reason"]).strip()
                if value.get("reason")
                else None
            ),
        )

    # ==================================================
    # PARAMETER HANDLING
    # ==================================================

    @staticmethod
    def _coerce_date(
        value,
    ) -> str | None:

        if isinstance(
            value,
            date,
        ):

            return value.isoformat()

        if not value:

            return None

        try:

            return (
                date
                .fromisoformat(
                    str(value).strip()
                )
                .isoformat()
            )

        except ValueError:

            return None

    @classmethod
    def _sanitize_parameters(
        cls,
        value,
    ) -> dict:

        if not isinstance(
            value,
            dict,
        ):

            return {}

        clean = {}

        for key in SAME_INTENT_INHERITABLE_PARAMETERS:

            if key not in value:

                continue

            item = value[key]

            if key in DATE_PARAMETERS:

                item = cls._coerce_date(
                    item
                )

            elif key in BOOLEAN_PARAMETERS:

                item = bool(item)

            elif key in LIST_PARAMETERS:

                item = (
                    [
                        str(entry).strip().lower()
                        for entry in item
                        if str(entry).strip()
                    ]
                    if isinstance(item, (list, tuple))
                    else []
                )

            elif item is not None:

                item = (
                    str(item).strip()
                    or None
                )

            if item in (None, "", [], False):

                continue

            clean[key] = item

        return clean

    @classmethod
    def _merge_parameters(
        cls,
        *,
        previous: dict,
        extracted: dict,
        context_used: ContextUsage,
    ) -> dict:

        #
        # Requirement: keep the previous parameters and replace only
        # what the user changed. The extracted values are what the
        # user changed, so they win; everything else carries over.
        #

        if not context_used.used:

            return dict(
                extracted
            )

        merged = dict(
            previous
        )

        merged.update(
            extracted
        )

        return merged

    @classmethod
    def _apply_relative_window(
        cls,
        *,
        parameters: dict,
        query: str,
        resolved_query: str,
        today: date,
    ) -> dict:

        #
        # Dates are owned by the backend, not the LLM. When the
        # latest message names a relative window ("what about this
        # month?"), that window wins over both the inherited dates
        # and whatever the resolver produced.
        #

        window = TemporalService.resolve_relative_window(
            query,
            today=today,
        )

        if window is None:

            window = TemporalService.resolve_relative_window(
                resolved_query,
                today=today,
            )

            if window is None:

                return parameters

            if (
                parameters.get("start_date")
                and parameters.get("end_date")
            ):

                # The rewrite only restated an inherited window.

                return parameters

        start, end = window

        parameters = dict(
            parameters
        )

        parameters["start_date"] = start.isoformat()

        parameters["end_date"] = end.isoformat()

        return parameters

    @staticmethod
    def _validate_window(
        parameters: dict,
    ) -> dict:

        start = parameters.get("start_date")

        end = parameters.get("end_date")

        if not (start and end):

            return parameters

        if start > end:

            parameters["start_date"] = end

            parameters["end_date"] = start

        return parameters

import json

from datetime import (
    date,
    datetime,
)

from decimal import Decimal

from uuid import UUID

from sqlalchemy import (
    bindparam,
    text,
)


def make_json_safe(value):

    if isinstance(
        value,
        (
            datetime,
            date,
        ),
    ):
        return value.isoformat()

    if isinstance(
        value,
        Decimal,
    ):
        return float(value)

    if isinstance(
        value,
        UUID,
    ):
        return str(value)

    if isinstance(
        value,
        dict,
    ):
        return {
            str(key): make_json_safe(item)
            for key, item in value.items()
        }

    if isinstance(
        value,
        list,
    ):
        return [
            make_json_safe(item)
            for item in value
        ]

    if isinstance(
        value,
        tuple,
    ):
        return [
            make_json_safe(item)
            for item in value
        ]

    if isinstance(
        value,
        set,
    ):
        return [
            make_json_safe(item)
            for item in value
        ]

    return value



def _coerce_json(
    value,
    default,
):

    # jsonb columns normally arrive decoded, but a raw driver
    # (or a NULL column) can hand back a string or None.

    if value is None:

        return default

    if isinstance(
        value,
        str,
    ):

        try:

            value = json.loads(
                value
            )

        except (
            ValueError,
            TypeError,
        ):

            return default

    if isinstance(
        default,
        list,
    ):

        return (
            list(value)
            if isinstance(value, (list, tuple))
            else default
        )

    return (
        value
        if isinstance(value, dict)
        else default
    )


class AIConversationAuditRepository:

    async def create(
        self,
        db,
        *,
        user_id: int,
        role: str,
        query: str,
        predicted_intent: str,
        parsed_intent: dict | None = None,
        selected_tools: list | None = None,
        tool_results: dict | None = None,
        summary: str = "",
        total_latency_ms: int | None = None,
        intent_latency_ms: int | None = None,
        tool_latency_ms: int | None = None,
        summarizer_latency_ms: int | None = None,
    ):

        safe_parsed_intent = make_json_safe(
            parsed_intent or {}
        )

        safe_selected_tools = make_json_safe(
            selected_tools or []
        )

        safe_tool_results = make_json_safe(
            tool_results or {}
        )

        statement = text(
            """
            INSERT INTO ai_conversation_audit (

                user_id,
                role,
                query,

                predicted_intent,
                parsed_intent,
                selected_tools,
                tool_results,
                summary,

                total_latency_ms,
                intent_latency_ms,
                tool_latency_ms,
                summarizer_latency_ms,

                evaluated,
                evaluation,
                attention_priority,
                created_at

            )
            VALUES (

                :user_id,
                :role,
                :query,

                :predicted_intent,
                CAST(:parsed_intent AS jsonb),
                CAST(:selected_tools AS jsonb),
                CAST(:tool_results AS jsonb),
                :summary,

                :total_latency_ms,
                :intent_latency_ms,
                :tool_latency_ms,
                :summarizer_latency_ms,

                FALSE,
                '{}'::jsonb,
                'NOT_NEEDED',
                NOW()

            )
            RETURNING id
            """
        )

        result = await db.execute(
            statement,
            {
                "user_id": user_id,

                "role": role,

                "query": query,

                "predicted_intent":
                    predicted_intent,

                "parsed_intent":
                    json.dumps(
                        safe_parsed_intent
                    ),

                "selected_tools":
                    json.dumps(
                        safe_selected_tools
                    ),

                "tool_results":
                    json.dumps(
                        safe_tool_results
                    ),

                "summary":
                    summary,

                "total_latency_ms":
                    total_latency_ms,

                "intent_latency_ms":
                    intent_latency_ms,

                "tool_latency_ms":
                    tool_latency_ms,

                "summarizer_latency_ms":
                    summarizer_latency_ms,
            },
        )

        await db.commit()

        return result.scalar_one()

    # ==================================================
    # RECENT TURNS (CONVERSATION CONTEXT)
    # ==================================================
    NON_CONTEXTUAL_INTENTS = ("unknown", "action_confirmation", "")

    async def list_recent_turns(
        self,
        db,
        *,
        user_id: int,
        role: str,
        limit: int = 5,
    ) -> list[dict]:
        statement = text(
            """
            SELECT
                id AS turn_id,
                query,
                predicted_intent,
                parsed_intent,
                selected_tools,
                summary,
                created_at
            FROM ai_conversation_audit
            WHERE
                user_id = :user_id
                AND role = :role
                AND query IS NOT NULL
                AND TRIM(query) != ''
                AND LOWER(COALESCE(predicted_intent, '')) NOT IN :ignored_intents
            ORDER BY
                created_at DESC,
                id DESC
            LIMIT :limit
            """
        ).bindparams(
            bindparam(
                "ignored_intents",
                expanding=True,
            )
        )

        result = await db.execute(
            statement,
            {
                "user_id": user_id,
                "role": role,
                "ignored_intents": list(
                    self.NON_CONTEXTUAL_INTENTS
                ),
                "limit": limit,
            },
        )

        rows = []
        for row in result.mappings().all():
            item = dict(row)
            # Ensure JSON columns deserialize safely
            item["parsed_intent"] = _coerce_json(item.get("parsed_intent"), default={})
            item["selected_tools"] = _coerce_json(item.get("selected_tools"), default=[])
            rows.append(item)
        
        return rows
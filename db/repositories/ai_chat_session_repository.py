import json
import logging

from sqlalchemy import (
    bindparam,
    text,
)

from db.repositories.ai_conversation_audit_repository import (
    AIConversationAuditRepository,
    _coerce_json,
    make_json_safe,
)


logger = logging.getLogger(__name__)


# Titles are rendered in the sidebar, so the first query is
# trimmed rather than stored in full.

TITLE_MAX_LENGTH = 80


def build_title(
    query: str,
) -> str:

    cleaned = " ".join(
        (query or "").split()
    )

    if not cleaned:

        return "New chat"

    if len(cleaned) <= TITLE_MAX_LENGTH:

        return cleaned

    return (
        cleaned[: TITLE_MAX_LENGTH - 1].rstrip()
        + "…"
    )


class AIChatSessionRepository:

    # ==================================================
    # SESSIONS (READ-ONLY from this repo now)
    # ==================================================

    async def get_session(
        self,
        db,
        *,
        session_id,
        user_id: int | None = None,
        role: str | None = None,
    ) -> dict | None:

        statement = text(
            """
            SELECT
                id,
                user_id,
                role,
                title,
                status,
                message_count,
                last_message_at,
                created_at,
                updated_at
            FROM ai_chat_session
            WHERE
                id = :session_id
                AND (
                    CAST(:user_id AS bigint) IS NULL
                    OR user_id = CAST(:user_id AS bigint)
                )
                AND (
                    CAST(:role AS varchar) IS NULL
                    OR role = CAST(:role AS varchar)
                )
                AND status != 'deleted'
            """
        )

        result = await db.execute(
            statement,
            {
                "session_id": session_id,
                "user_id": user_id,
                "role": role,
            },
        )

        row = result.mappings().first()

        if not row:

            return None

        return dict(row)

    async def list_sessions(
        self,
        db,
        *,
        user_id: int,
        role: str,
        limit: int = 20,
        offset: int = 0,
        include_archived: bool = False,
    ) -> list[dict]:

        statement = text(
            """
            SELECT
                id,
                user_id,
                role,
                title,
                status,
                message_count,
                last_message_at,
                created_at,
                updated_at
            FROM ai_chat_session
            WHERE
                user_id = :user_id
                AND role = :role
                AND status != 'deleted'
                AND (
                    :include_archived
                    OR status = 'active'
                )
            ORDER BY
                COALESCE(
                    last_message_at,
                    created_at
                ) DESC,
                created_at DESC
            LIMIT :limit
            OFFSET :offset
            """
        )

        result = await db.execute(
            statement,
            {
                "user_id": user_id,
                "role": role,
                "include_archived": include_archived,
                "limit": limit,
                "offset": offset,
            },
        )

        return [
            dict(row)
            for row in result.mappings().all()
        ]

    async def update_session_title(
        self,
        db,
        *,
        session_id,
        title: str,
        user_id: int | None = None,
        role: str | None = None,
        only_if_empty: bool = False,
    ) -> bool:

        statement = text(
            """
            UPDATE ai_chat_session
            SET title = :title
            WHERE
                id = :session_id
                AND status != 'deleted'
                AND (
                    CAST(:user_id AS bigint) IS NULL
                    OR user_id = CAST(:user_id AS bigint)
                )
                AND (
                    CAST(:role AS varchar) IS NULL
                    OR role = CAST(:role AS varchar)
                )
                AND (
                    NOT :only_if_empty
                    OR title IS NULL
                    OR TRIM(title) = ''
                )
            RETURNING id
            """
        )

        result = await db.execute(
            statement,
            {
                "session_id": session_id,
                "title": title,
                "user_id": user_id,
                "role": role,
                "only_if_empty": only_if_empty,
            },
        )

        updated = (
            result.first()
            is not None
        )

        await db.commit()

        return updated

    async def set_session_status(
        self,
        db,
        *,
        session_id,
        status: str,
        user_id: int | None = None,
        role: str | None = None,
    ) -> bool:

        statement = text(
            """
            UPDATE ai_chat_session
            SET status = :status
            WHERE
                id = :session_id
                AND status != 'deleted'
                AND (
                    CAST(:user_id AS bigint) IS NULL
                    OR user_id = CAST(:user_id AS bigint)
                )
                AND (
                    CAST(:role AS varchar) IS NULL
                    OR role = CAST(:role AS varchar)
                )
            RETURNING id
            """
        )

        result = await db.execute(
            statement,
            {
                "session_id": session_id,
                "status": status,
                "user_id": user_id,
                "role": role,
            },
        )

        updated = (
            result.first()
            is not None
        )

        await db.commit()

        return updated

    # ==================================================
    # MESSAGES (READ-ONLY - list only for transcript/cache rebuild)
    # ==================================================

    async def list_messages(
        self,
        db,
        *,
        session_id,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict]:

        statement = text(
            """
            SELECT
                id,
                session_id,
                query,
                answer,
                context_resolution,
                selected_tools,
                parsed_intent,
                predicted_intent,
                created_at
            FROM ai_chat_message
            WHERE session_id = :session_id
            ORDER BY id DESC
            LIMIT :limit
            OFFSET :offset
            """
        )

        result = await db.execute(
            statement,
            {
                "session_id": session_id,
                "limit": limit,
                "offset": offset,
            },
        )

        return [
            dict(row)
            for row in result.mappings().all()
        ]

    # ==================================================
    # CONVERSATION CONTEXT (CACHE REBUILD)
    # ==================================================

    async def list_recent_turns(
        self,
        db,
        *,
        session_id,
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
                answer AS summary,
                created_at
            FROM ai_chat_message
            WHERE
                session_id = :session_id
                AND query IS NOT NULL
                AND TRIM(query) != ''
                AND LOWER(
                    COALESCE(
                        predicted_intent,
                        ''
                    )
                ) NOT IN :ignored_intents
            ORDER BY
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
                "session_id": session_id,
                "ignored_intents": list(
                    AIConversationAuditRepository.NON_CONTEXTUAL_INTENTS
                ),
                "limit": limit,
            },
        )

        rows = []

        for row in result.mappings().all():

            item = dict(row)

            item["predicted_intent"] = (
                item.get(
                    "predicted_intent"
                )
                or ""
            )

            item["parsed_intent"] = _coerce_json(
                item.get(
                    "parsed_intent"
                ),
                default={},
            )

            item["selected_tools"] = _coerce_json(
                item.get(
                    "selected_tools"
                ),
                default=[],
            )

            rows.append(item)

        return rows

    # ==================================================
    # SESSION MEMORY (CACHE REBUILD)
    # ==================================================

    ACTION_INTENTS = (
        "journal_create",
        "personal_event_create",
        "action_confirmation",
    )

    async def list_action_turns(
        self,
        db,
        *,
        session_id,
        limit: int = 50,
    ) -> list[dict]:

        statement = text(
            """
            SELECT
                m.id AS turn_id,
                m.query,
                LOWER(
                    COALESCE(
                        m.predicted_intent,
                        ''
                    )
                ) AS predicted_intent,
                m.answer,
                m.created_at,
                a.tool_results
            FROM ai_chat_message m
            LEFT JOIN ai_conversation_audit a
                ON a.id = m.audit_id
            WHERE
                m.session_id = :session_id
                AND LOWER(
                    COALESCE(
                        m.predicted_intent,
                        ''
                    )
                ) IN :action_intents
            ORDER BY
                m.id DESC
            LIMIT :limit
            """
        ).bindparams(
            bindparam(
                "action_intents",
                expanding=True,
            )
        )

        result = await db.execute(
            statement,
            {
                "session_id": session_id,
                "action_intents": list(
                    self.ACTION_INTENTS
                ),
                "limit": limit,
            },
        )

        rows = []

        for row in result.mappings().all():

            item = dict(row)

            item["tool_results"] = _coerce_json(
                item.get(
                    "tool_results"
                ),
                default={},
            )

            rows.append(item)

        # The query took the newest rows; replay them oldest first.

        rows.reverse()

        return rows

import json
import logging

from sqlalchemy import (
    bindparam,
    text,
)

from sqlalchemy.exc import IntegrityError

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
    # SESSIONS
    # ==================================================

    async def create_session(
        self,
        db,
        *,
        user_id: int,
        role: str,
        title: str | None = None,
    ) -> dict:

        statement = text(
            """
            INSERT INTO ai_chat_session (

                user_id,
                role,
                title,
                status

            )
            VALUES (

                :user_id,
                :role,
                :title,
                'active'

            )
            RETURNING
                id,
                user_id,
                role,
                title,
                status,
                message_count,
                last_message_at,
                created_at,
                updated_at
            """
        )

        result = await db.execute(
            statement,
            {
                "user_id": user_id,
                "role": role,
                "title": title,
            },
        )

        row = dict(
            result.mappings().one()
        )

        await db.commit()

        return row

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
                id = CAST(:session_id AS uuid)
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
                "session_id": str(session_id),
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
                id = CAST(:session_id AS uuid)
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
                "session_id": str(session_id),
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
                id = CAST(:session_id AS uuid)
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
                "session_id": str(session_id),
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
    # TURNS
    # ==================================================

    INSERT_RETRIES = 3

    async def create_message(
        self,
        db,
        *,
        session_id,
        user_id: int,
        role: str,
        query: str,
        status: str = "pending",
    ) -> dict:

        statement = text(
            """
            INSERT INTO ai_chat_message (

                session_id,
                user_id,
                role,
                turn_index,
                query,
                status

            )
            VALUES (

                CAST(:session_id AS uuid),
                :user_id,
                :role,
                (
                    SELECT
                        COALESCE(
                            MAX(turn_index),
                            0
                        ) + 1
                    FROM ai_chat_message
                    WHERE session_id = CAST(:session_id AS uuid)
                ),
                :query,
                :status

            )
            RETURNING
                id,
                session_id,
                turn_index,
                created_at
            """
        )

        parameters = {
            "session_id": str(session_id),
            "user_id": user_id,
            "role": role,
            "query": query,
            "status": status,
        }

        for attempt in range(
            self.INSERT_RETRIES
        ):

            try:

                result = await db.execute(
                    statement,
                    parameters,
                )

                row = dict(
                    result.mappings().one()
                )

                await db.commit()

                return row

            except IntegrityError:

                await db.rollback()

                if (
                    attempt
                    ==
                    self.INSERT_RETRIES - 1
                ):

                    raise

                logger.warning(
                    "Turn index collision on session %s; retrying.",
                    session_id,
                )

    async def complete_message(
        self,
        db,
        *,
        message_id: int,
        answer: str | None,
        status: str = "completed",
        audit_id: int | None = None,
        error_message: str | None = None,
    ) -> bool:

        statement = text(
            """
            UPDATE ai_chat_message
            SET
                answer = :answer,
                status = :status,
                error_message = :error_message,
                audit_id = COALESCE(
                    :audit_id,
                    audit_id
                )
            WHERE id = :message_id
            RETURNING id
            """
        )

        result = await db.execute(
            statement,
            {
                "message_id": message_id,
                "answer": answer,
                "status": status,
                "audit_id": audit_id,
                "error_message": error_message,
            },
        )

        updated = (
            result.first()
            is not None
        )

        await db.commit()

        return updated

    async def attach_intent(
        self,
        db,
        *,
        message_id: int,
        predicted_intent: str | None = None,
        parsed_intent: dict | None = None,
        selected_tools: list | None = None,
        audit_id: int | None = None,
    ) -> bool:

        statement = text(
            """
            UPDATE ai_chat_message
            SET
                predicted_intent = COALESCE(
                    :predicted_intent,
                    predicted_intent
                ),
                parsed_intent = COALESCE(
                    CAST(:parsed_intent AS jsonb),
                    parsed_intent
                ),
                selected_tools = COALESCE(
                    CAST(:selected_tools AS jsonb),
                    selected_tools
                ),
                audit_id = COALESCE(
                    :audit_id,
                    audit_id
                )
            WHERE id = :message_id
            RETURNING id
            """
        )

        result = await db.execute(
            statement,
            {
                "message_id": message_id,

                "predicted_intent":
                    predicted_intent,

                "parsed_intent": (
                    json.dumps(
                        make_json_safe(
                            parsed_intent
                        )
                    )
                    if parsed_intent is not None
                    else None
                ),

                "selected_tools": (
                    json.dumps(
                        make_json_safe(
                            selected_tools
                        )
                    )
                    if selected_tools is not None
                    else None
                ),

                "audit_id": audit_id,
            },
        )

        updated = (
            result.first()
            is not None
        )

        await db.commit()

        return updated

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
                turn_index,
                query,
                answer,
                status,
                error_message,
                audit_id,
                created_at,
                updated_at
            FROM ai_chat_message
            WHERE session_id = CAST(:session_id AS uuid)
            ORDER BY
                turn_index ASC,
                id ASC
            LIMIT :limit
            OFFSET :offset
            """
        )

        result = await db.execute(
            statement,
            {
                "session_id": str(session_id),
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
                session_id = CAST(:session_id AS uuid)
                AND status = 'completed'
                AND query IS NOT NULL
                AND TRIM(query) != ''
                AND LOWER(
                    COALESCE(
                        predicted_intent,
                        ''
                    )
                ) NOT IN :ignored_intents
            ORDER BY
                turn_index DESC,
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
                "session_id": str(session_id),
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

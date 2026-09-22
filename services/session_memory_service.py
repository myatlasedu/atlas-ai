"""
Session memory of actions.

The five-turn conversation context answers "what was the student
talking about?". This service answers "what did Atlas actually do in
this chat?": every journal entry or personal event the student asked
for, and whether it was saved, cancelled or is still waiting for a
confirmation.

Redis holds the records; ai_chat_message (joined to its audit row)
rebuilds them when the key has expired.
"""

import logging

from datetime import (
    datetime,
    timezone,
)

from uuid import uuid4

from cache.session_memory_cache import (
    SessionMemoryCache,
)

from db.repositories.ai_chat_session_repository import (
    AIChatSessionRepository,
)

from db.session import AsyncSessionLocal

from utils import format_datetime


logger = logging.getLogger(__name__)


def _format_event_time(
    value,
) -> str:

    # The event extractor emits IST wall-clock times with no
    # timezone; those are shown as written. Only an aware
    # timestamp goes through the UTC -> IST conversion.

    try:

        parsed = (
            value
            if isinstance(value, datetime)
            else datetime.fromisoformat(
                str(value)
            )
        )

    except (ValueError, TypeError):

        return str(value)

    if parsed.tzinfo is not None:

        return format_datetime(
            parsed
        )

    return parsed.strftime(
        "%d %b %Y at %I:%M %p"
    )


STATUS_PENDING = "pending"

STATUS_COMPLETED = "completed"

STATUS_CANCELLED = "cancelled"


# Human labels the recall answer is built from.

ACTION_LABELS = {
    "create_journal": "journal entry",
    "create_personal_event": "personal event",
}


class SessionMemoryService:

    repository = AIChatSessionRepository()

    # ==================================================
    # DESCRIBING AN ACTION
    # ==================================================

    @staticmethod
    def describe_action(
        action_type: str | None,
        payload: dict | None,
    ) -> str:

        payload = payload or {}

        if action_type == "create_journal":

            content = str(
                payload.get("content")
                or ""
            ).strip()

            if content:

                return (
                    f"a journal entry: \"{content}\""
                )

            return "a journal entry"

        if action_type == "create_personal_event":

            title = str(
                payload.get("title")
                or ""
            ).strip()

            event_type = str(
                payload.get("event_type")
                or ""
            ).strip().lower()

            when = ""

            start = payload.get(
                "start_datetime"
            )

            if start:

                when = f" on {_format_event_time(start)}"

            kind = (
                f"{event_type} event"
                if event_type
                else "personal event"
            )

            if title:

                return f"a {kind} \"{title}\"{when}"

            return f"a {kind}{when}"

        label = ACTION_LABELS.get(
            action_type,
            str(action_type or "action").replace("_", " "),
        )

        return f"a {label}"

    # ==================================================
    # WRITE SIDE
    # ==================================================

    @classmethod
    async def record_pending(
        cls,
        session_id,
        *,
        action_type: str,
        payload: dict | None,
        query: str,
        turn_id=None,
    ) -> None:

        # The student asked for something and Atlas proposed it.
        # Nothing is saved until the confirmation turn resolves it.

        if not session_id or not action_type:

            return

        records = await cls._load_records(
            session_id
        )

        records.append(
            cls._new_record(
                action_type=action_type,
                payload=payload,
                query=query,
                turn_id=turn_id,
                status=STATUS_PENDING,
            )
        )

        await SessionMemoryCache.save(
            session_id,
            records,
        )

        logger.info(
            "Session memory: pending %s recorded for session=%s",
            action_type,
            session_id,
        )

    @classmethod
    async def resolve_pending(
        cls,
        session_id,
        *,
        action_type: str | None,
        status: str,
        payload: dict | None = None,
        turn_id=None,
        query: str | None = None,
    ) -> None:

        # The confirmation turn: the latest pending record of
        # this action type becomes completed or cancelled. If no
        # pending record exists (Redis was cold when the request
        # came in) a completed action is still remembered, since
        # it did happen.

        if not session_id:

            return

        records = await cls._load_records(
            session_id
        )

        resolved = cls._resolve_in_place(
            records,
            action_type=action_type,
            status=status,
            payload=payload,
            turn_id=turn_id,
        )

        if not resolved and status == STATUS_COMPLETED:

            records.append(
                cls._new_record(
                    action_type=action_type,
                    payload=payload,
                    query=query or "",
                    turn_id=turn_id,
                    status=STATUS_COMPLETED,
                    resolved_turn_id=turn_id,
                )
            )

            resolved = True

        if not resolved:

            return

        await SessionMemoryCache.save(
            session_id,
            records,
        )

        logger.info(
            "Session memory: %s marked %s for session=%s",
            action_type,
            status,
            session_id,
        )

    # ==================================================
    # READ SIDE
    # ==================================================

    @classmethod
    async def load(
        cls,
        turn=None,
    ) -> list[dict]:

        # Oldest first. Records for a session with no history
        # (or no session at all) are an empty list.

        session_id = getattr(
            turn,
            "session_id",
            None,
        )

        if not session_id:

            return []

        return await cls._load_records(
            session_id
        )

    @classmethod
    async def _load_records(
        cls,
        session_id,
    ) -> list[dict]:

        records = await SessionMemoryCache.load(
            session_id
        )

        if records is not None:

            return records

        records = await cls._rebuild(
            session_id
        )

        await SessionMemoryCache.save(
            session_id,
            records,
        )

        return records

    @classmethod
    async def _rebuild(
        cls,
        session_id,
    ) -> list[dict]:

        try:

            async with AsyncSessionLocal() as db:

                rows = await cls.repository.list_action_turns(
                    db,
                    session_id=session_id,
                )

        except Exception:

            logger.exception(
                "Failed to rebuild session memory; continuing without it."
            )

            return []

        records = cls.replay_action_turns(
            rows
        )

        logger.info(
            "Rebuilt %s action record(s) from ai_chat_message for session=%s",
            len(records),
            session_id,
        )

        return records

    @classmethod
    def replay_action_turns(
        cls,
        rows: list[dict],
    ) -> list[dict]:

        # Replays request and confirmation turns (oldest first)
        # into the same records the live path would have written.

        records: list[dict] = []

        for row in rows:

            tool_results = row.get(
                "tool_results"
            ) or {}

            if not isinstance(
                tool_results,
                dict,
            ):

                continue

            for tool_result in tool_results.values():

                if not isinstance(
                    tool_result,
                    dict,
                ):

                    continue

                action_type = tool_result.get(
                    "action_type"
                )

                if tool_result.get(
                    "action_required"
                ):

                    records.append(
                        cls._new_record(
                            action_type=action_type,
                            payload=cls.payload_from_result(
                                tool_result
                            ),
                            query=row.get("query") or "",
                            turn_id=row.get("turn_id"),
                            status=STATUS_PENDING,
                            created_at=row.get("created_at"),
                        )
                    )

                elif tool_result.get(
                    "action_completed"
                ):

                    payload = tool_result.get(
                        "payload"
                    )

                    if not cls._resolve_in_place(
                        records,
                        action_type=action_type,
                        status=STATUS_COMPLETED,
                        payload=payload,
                        turn_id=row.get("turn_id"),
                        resolved_at=row.get("created_at"),
                    ):

                        records.append(
                            cls._new_record(
                                action_type=action_type,
                                payload=payload,
                                query=row.get("query") or "",
                                turn_id=row.get("turn_id"),
                                status=STATUS_COMPLETED,
                                resolved_turn_id=row.get("turn_id"),
                                created_at=row.get("created_at"),
                            )
                        )

                elif tool_result.get(
                    "action_cancelled"
                ):

                    cls._resolve_in_place(
                        records,
                        action_type=action_type,
                        status=STATUS_CANCELLED,
                        turn_id=row.get("turn_id"),
                        resolved_at=row.get("created_at"),
                    )

        return records[-SessionMemoryCache.MAX_RECORDS:]

    # ==================================================
    # HELPERS
    # ==================================================

    @staticmethod
    def payload_from_result(
        tool_result: dict,
    ) -> dict:

        # Create tools expose the extracted payload; the journal
        # tool also mirrors it under llm_context for the
        # summarizer, which is the fallback for older audit rows.

        payload = tool_result.get(
            "payload"
        )

        if isinstance(
            payload,
            dict,
        ):

            return payload

        llm_context = tool_result.get(
            "llm_context"
        )

        if isinstance(
            llm_context,
            dict,
        ):

            return {
                key: value
                for key, value in llm_context.items()
                if key != "action"
            }

        return {}

    @classmethod
    def _new_record(
        cls,
        *,
        action_type,
        payload,
        query,
        turn_id,
        status,
        resolved_turn_id=None,
        created_at=None,
    ) -> dict:

        payload = (
            payload
            if isinstance(payload, dict)
            else {}
        )

        now = cls._iso(
            created_at
        )

        return {
            "id": uuid4().hex[:12],
            "action_type": action_type,
            "status": status,
            "description": cls.describe_action(
                action_type,
                payload,
            ),
            "payload": payload,
            "query": query,
            "requested_turn_id": turn_id,
            "resolved_turn_id": resolved_turn_id,
            "requested_at": now,
            "resolved_at": (
                now
                if resolved_turn_id is not None
                else None
            ),
        }

    @classmethod
    def _resolve_in_place(
        cls,
        records: list[dict],
        *,
        action_type,
        status,
        payload=None,
        turn_id=None,
        resolved_at=None,
    ) -> bool:

        for record in reversed(records):

            if record.get("status") != STATUS_PENDING:

                continue

            if (
                action_type
                and record.get("action_type")
                and record.get("action_type") != action_type
            ):

                continue

            record["status"] = status

            record["resolved_turn_id"] = turn_id

            record["resolved_at"] = cls._iso(
                resolved_at
            )

            if isinstance(
                payload,
                dict,
            ) and payload:

                # The executed payload is the truth: it is what
                # was written to the database.

                record["payload"] = payload

                record["description"] = cls.describe_action(
                    record.get("action_type"),
                    payload,
                )

            return True

        return False

    @staticmethod
    def _iso(
        value=None,
    ) -> str:

        if isinstance(
            value,
            datetime,
        ):

            return value.isoformat()

        if value:

            return str(value)

        return datetime.now(
            timezone.utc
        ).isoformat()

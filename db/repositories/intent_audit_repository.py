from sqlalchemy import text
import json


class IntentAuditRepository:

    def __init__(self, db):
        self.db = db

    async def create(
        self,
        *,
        query: str,
        role: str,
        user_id: int | None,
        predicted_intent: str,
        confidence: float,
        parser_output: dict,
    ):

        await self.db.execute(
            text(
                """
                INSERT INTO ai_intentaudit
                (
                    query,
                    role,
                    user_id,
                    predicted_intent,
                    confidence,
                    parser_output,
                    review_status,
                    created_at
                )
                VALUES
                (
                    :query,
                    :role,
                    :user_id,
                    :predicted_intent,
                    :confidence,
                    CAST(:parser_output AS jsonb),
                    'pending',
                    NOW()
                )
                """
            ),
            {
                "query": query,
                "role": role,
                "user_id": user_id,
                "predicted_intent": predicted_intent,
                "confidence": confidence,
                "parser_output": json.dumps(parser_output),
            },
        )

        await self.db.commit()
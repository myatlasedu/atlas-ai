import logging

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
)

from schemas.ai import (
    AIRequest,
    MentorAIRequest,
    GuardianAIRequest,
)

from core.security import verify_internal_api_key

from services.student_ai_service import StudentAIService
from services.mentor_ai_service import MentorAIService
from services.guardian_ai_service import GuardianAIService
import traceback

logger = logging.getLogger(__name__)

router = APIRouter()

ai_service = StudentAIService()
mentor_ai_service = MentorAIService()
guardian_ai_service = GuardianAIService()


@router.post("/query")
async def ai_query(
    payload: AIRequest,
    request: Request,
    _: str = Depends(verify_internal_api_key),
):
    try:
        classifier = request.app.state.intent_classifier

        return await ai_service.answer(
            query=payload.query,
            context=payload.context,
            classifier=classifier,
            session_id=payload.session_id
        )
        
    except Exception as e:
        print("Error - ", e)
        print("Traceback - ", traceback.print_exc())
        raise HTTPException(
            status_code=500,
            detail="Student AI query failed",
        )


@router.post("/mentor_query")
async def mentor_ai_query(
    payload: MentorAIRequest,
    _: str = Depends(verify_internal_api_key),
):
    try:

        return await (
            mentor_ai_service.answer(
                query=payload.query,
                context=payload.context,
                session_id=payload.session_id
            )
        )

    except Exception:
        logger.exception("Mentor AI query failed")

        raise HTTPException(
            status_code=500,
            detail="Mentor AI query failed",
        )


@router.post("/guardian_query")
async def guardian_ai_query(
    payload: GuardianAIRequest,
    _: str = Depends(verify_internal_api_key),
):
    try:

        return await (
            guardian_ai_service.answer(
                query=payload.query,
                context=payload.context,
                session_id=payload.session_id
            )
        )

    except Exception:
        logger.exception("Guardian AI query failed")

        raise HTTPException(
            status_code=500,
            detail="Guardian AI query failed",
        )
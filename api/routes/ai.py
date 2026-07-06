from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from schemas.ai import AIRequest, MentorAIRequest, GuardianAIRequest
from core.security import verify_internal_api_key
from services.student_ai_service import StudentAIService
from services.mentor_ai_service import MentorAIService
from services.guardian_ai_service import GuardianAIService

from intents.guardian.enums import (
    GuardianIntent
)

from intents.guardian.schemas import (
    ParsedGuardianIntent
)

from routing.guardian_tool_router import (
    get_tools_for_intent
)
import traceback


router = APIRouter()

ai_service = StudentAIService()

mentor_ai_service = MentorAIService()

guardian_ai_service = GuardianAIService()

@router.post("/query")
async def ai_query(
    payload: AIRequest,
    _: str = Depends(
        verify_internal_api_key
    )
):

    try:
        return await ai_service.answer(
            query=payload.query,
            context=payload.context
        )

    except Exception as e:
        print("Error - ", e)
        print("Traceback - ", traceback.print_exc())
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
    
@router.post("/mentor_query")
async def mentor_ai_query(
    payload: MentorAIRequest,
    _: str = Depends(
        verify_internal_api_key
    )
):

    try:

        return await (
            mentor_ai_service.answer(
                query=payload.query,
                context=payload.context
            )
        )

    except Exception as e:

        print(
            "Error - ",
            e
        )

        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
    
@router.post("/guardian_query")
async def guardian_ai_query(
    payload: GuardianAIRequest,
    _: str = Depends(
        verify_internal_api_key
    )
):

    try:

        return await (
            guardian_ai_service.answer(
                query=payload.query,
                context=payload.context
            )
        )

    except Exception as e:

        print(
            "Error - ",
            e
        )

        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
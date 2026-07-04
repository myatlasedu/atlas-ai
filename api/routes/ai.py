from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from schemas.ai import AIRequest, MentorAIRequest
from core.security import verify_internal_api_key
from services.student_ai_service import StudentAIService
from services.mentor_ai_service import MentorAIService
import traceback

router = APIRouter()

ai_service = StudentAIService()

mentor_ai_service = MentorAIService()

@router.post("/query")
async def ai_query(
    payload: AIRequest,
    # _: str = Depends(
    #     verify_internal_api_key
    # )
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
    payload: MentorAIRequest
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
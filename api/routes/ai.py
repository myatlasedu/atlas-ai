from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from schemas.ai import AIRequest
from core.security import verify_internal_api_key
from services.ai_service import AIService
import traceback

router = APIRouter()

ai_service = AIService()


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
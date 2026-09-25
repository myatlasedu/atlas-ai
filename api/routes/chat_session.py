import logging

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)

from core.security import (
    verify_internal_api_key,
)

from schemas.chat_session import (
    ChatSession,
    ChatTranscript,
    UpdateSessionRequest,
)

from services.chat_session_service import (
    ChatSessionService,
)


logger = logging.getLogger(__name__)

router = APIRouter()


# ==================================================
# LIST SESSIONS
# ==================================================

@router.get(
    "/sessions",
    response_model=list[ChatSession],
)
async def list_sessions(
    user_id: int = Query(...),
    role: str = Query(...),
    limit: int = Query(
        20,
        ge=1,
        le=50,
    ),
    offset: int = Query(
        0,
        ge=0,
    ),
    include_archived: bool = Query(
        False,
    ),
    _: str = Depends(
        verify_internal_api_key
    ),
):

    return await ChatSessionService.list_sessions(
        user_id=user_id,
        role=role,
        limit=limit,
        offset=offset,
        include_archived=include_archived,
    )


# ==================================================
# TRANSCRIPT
# ==================================================

@router.get(
    "/sessions/{session_id}",
    response_model=ChatTranscript,
)
async def get_session(
    session_id: int,
    user_id: int = Query(...),
    role: str = Query(...),
    limit: int = Query(
        100,
        ge=1,
        le=200,
    ),
    offset: int = Query(
        0,
        ge=0,
    ),
    _: str = Depends(
        verify_internal_api_key
    ),
):

    transcript = await ChatSessionService.get_transcript(
        session_id=session_id,
        user_id=user_id,
        role=role,
        limit=limit,
        offset=offset,
    )

    if transcript is None:

        raise HTTPException(
            status_code=404,
            detail="Session not found.",
        )

    return transcript


# ==================================================
# RENAME / ARCHIVE
# ==================================================

@router.patch(
    "/sessions/{session_id}",
)
async def update_session(
    session_id: int,
    payload: UpdateSessionRequest,
    _: str = Depends(
        verify_internal_api_key
    ),
):

    if (
        payload.title is None
        and
        payload.status is None
    ):

        raise HTTPException(
            status_code=400,
            detail="Nothing to update.",
        )

    updated = False

    if payload.title is not None:

        updated = await ChatSessionService.rename_session(
            session_id=session_id,
            user_id=payload.user_id,
            role=payload.role,
            title=payload.title,
        )

    if payload.status is not None:

        updated = await ChatSessionService.set_status(
            session_id=session_id,
            user_id=payload.user_id,
            role=payload.role,
            status=payload.status,
        )

    if not updated:

        raise HTTPException(
            status_code=404,
            detail="Session not found.",
        )

    return {
        "success": True,
    }


# ==================================================
# DELETE
# ==================================================

@router.delete(
    "/sessions/{session_id}",
)
async def delete_session(
    session_id: int,
    user_id: int = Query(...),
    role: str = Query(...),
    _: str = Depends(
        verify_internal_api_key
    ),
):

    # Soft delete - the audit trail stays intact and the
    # thread simply drops out of every listing.

    deleted = await ChatSessionService.set_status(
        session_id=session_id,
        user_id=user_id,
        role=role,
        status="deleted",
    )

    if not deleted:

        raise HTTPException(
            status_code=404,
            detail="Session not found.",
        )

    return {
        "success": True,
    }

import logging
from fastapi import APIRouter, HTTPException, Request
from app.models.schemas import ChatRequest, ChatResponse, SessionSummary, SessionDetail
from app.services import session as session_service
from app.services.agent import run_agent

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    await session_service.get_or_create_session(request.session_id)
    history = await session_service.get_history(request.session_id)

    try:
        result = await run_agent(user_message=request.message, history=history)
    except Exception as e:
        logger.exception("Agent error")
        raise HTTPException(status_code=500, detail=str(e))

    await session_service.save_messages(
        session_id=request.session_id,
        user_content=request.message,
        assistant_content=result["reply"],
    )

    return ChatResponse(
        session_id=request.session_id,
        reply=result["reply"],
        commands_executed=result["commands_executed"],
    )


@router.get("/sessions", response_model=list[SessionSummary])
async def list_sessions():
    return await session_service.get_all_sessions()


@router.get("/sessions/{session_id}", response_model=SessionDetail)
async def get_session(session_id: str):
    detail = await session_service.get_session_detail(session_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Session not found")
    return detail


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    await session_service.delete_session(session_id)
    return {"deleted": session_id}


@router.get("/sessions", response_model=list[SessionSummary])
async def list_sessions():
    sessions = await session_service.get_all_sessions()
    return sessions


@router.get("/sessions/{session_id}", response_model=SessionDetail)
async def get_session(session_id: str):
    detail = await session_service.get_session_detail(session_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Session not found")
    return detail


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    await session_service.delete_session(session_id)
    return {"deleted": session_id}
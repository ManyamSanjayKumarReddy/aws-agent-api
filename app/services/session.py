import logging
from app.models.db import Session, Message

logger = logging.getLogger(__name__)


async def get_or_create_session(session_id: str) -> Session:
    session, _ = await Session.get_or_create(id=session_id)
    return session


async def get_history(session_id: str) -> list[dict]:
    messages = await Message.filter(session_id=session_id).order_by("created_at")
    return [{"role": m.role, "content": m.content} for m in messages]


async def save_messages(session_id: str, user_content: str, assistant_content: str):
    await Message.create(session_id=session_id, role="user", content=user_content)
    await Message.create(session_id=session_id, role="assistant", content=assistant_content)

    session = await Session.get(id=session_id)
    if not session.title:
        session.title = user_content[:80].strip()
        await session.save()


async def get_all_sessions() -> list[dict]:
    sessions = await Session.all().order_by("-created_at")
    result = []
    for s in sessions:
        count = await Message.filter(session_id=s.id).count()
        result.append({
            "session_id": s.id,
            "title": s.title,
            "message_count": count,
            "created_at": s.created_at,
        })
    return result


async def get_session_detail(session_id: str) -> dict | None:
    session = await Session.get_or_none(id=session_id)
    if not session:
        return None
    messages = await Message.filter(session_id=session_id).order_by("created_at")
    return {
        "session_id": session.id,
        "title": session.title,
        "created_at": session.created_at,
        "messages": [
            {"role": m.role, "content": m.content, "created_at": m.created_at}
            for m in messages
        ],
    }


async def delete_session(session_id: str):
    await Message.filter(session_id=session_id).delete()
    await Session.filter(id=session_id).delete()
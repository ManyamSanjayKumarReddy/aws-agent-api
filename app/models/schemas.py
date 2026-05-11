from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ChatRequest(BaseModel):
    session_id: str
    message: str


class MessageOut(BaseModel):
    role: str
    content: str
    created_at: datetime


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    commands_executed: list[str] = []


class SessionSummary(BaseModel):
    session_id: str
    title: Optional[str]
    message_count: int
    created_at: datetime


class SessionDetail(BaseModel):
    session_id: str
    title: Optional[str]
    created_at: datetime
    messages: list[MessageOut]
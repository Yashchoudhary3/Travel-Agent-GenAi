from typing import Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    status: Literal["need_info", "planning", "complete"]
    missing_fields: list[str] = Field(default_factory=list)

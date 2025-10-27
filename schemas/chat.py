# schemas/chat.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from .user import User

class ChatMessage(BaseModel):
    id: int
    match_id: int
    sender_id: int
    content: str
    created_at: datetime
    sender: Optional[User] = None

    class Config:
        from_attributes = True

class ChatMessageCreate(BaseModel):
    content: str

class ChatRoom(BaseModel):
    match_id: int
    other_user: User
    last_message: Optional[ChatMessage] = None
    unread_count: int = 0

    class Config:
        from_attributes = True

"""schema.py : contains all the models/classes for data validation,structure"""

from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime



class ChatRequest(BaseModel):
    """validate user input"""
    text: str
    conversation_id: Optional[int] = None # Optional: cause no ID for new conversation, but required for ongoing ones



"""validate chat response"""
class ChatResponse(BaseModel):
    reply: str
    conversation_id: int


class ChatConversation(BaseModel):
    id: int
    title: str

    class Config:
        orm_mode = True


class ChatMessage(BaseModel):
    text: str
    sender: Literal["user", "bot"]
    timestamp: datetime

    class Config:
        orm_mode = True
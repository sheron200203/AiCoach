"""schema.py : contains all the models/classes for data validation,structure"""
from pydantic import BaseModel
from typing import Optional, Literal

class ChatRequest(BaseModel):
    """validate user input"""
    text: str
    conversation_id: Optional[int] = None # Optional: cause no ID for new conversation, but required for ongoing ones



"""validate chat response"""
class ChatResponse(BaseModel):
    reply: str
    conversation_id: int

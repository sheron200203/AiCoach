from typing import List

from fastapi import Depends, APIRouter
from app.auth.dependencies import get_current_user, get_session_local
from app.auth.schemas import User
from sqlalchemy.orm import Session
from app.chatbot.engine import get_similar_response
from app.chatbot.schemas import ChatResponse, ChatRequest
from app.db.models import Conversation
from app.chatbot.schemas import ChatConversation

router = APIRouter(
    prefix="/chatbot",
    tags=["chatbot"],
)



@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest,
                  current_user: User = Depends(get_current_user),
                  db: Session = Depends(get_session_local),):
    """ Process a user chat request, create a conversation if needed, and return the bot's reply. """

    conversation_id = request.conversation_id

    # If no conversation_id, create a new conversation
    if not conversation_id:
        new_convo = Conversation(
            user_id=current_user.id,
            title=request.text[:30]
        )
        db.add(new_convo)
        db.commit()
        db.refresh(new_convo)
        conversation_id = new_convo.id

    # Get the bot's reply
    reply = get_similar_response(request.text)

    return {
        "reply": reply,
        "conversation_id": conversation_id
    }



@router.get("/conversations", response_model=List[ChatConversation])
def list_conversations(db: Session = Depends(get_session_local),current_user: User = Depends(get_current_user)):
    """ Retrieve all chat conversations for the currently authenticated user,sorted from newest to oldest."""

    conversations = (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .order_by(Conversation.created_at.desc())
        .all()
    )
    return conversations
"""crud.py : crud operations relating to  db"""

from sqlalchemy.orm import Session
from app.db.models import MessageHistory




"""create msg in db"""
def save_message(user_id: int, conversation_id: int, message: str, is_bot: bool, db: Session):
    new_message = MessageHistory(
        conversation_id=conversation_id,
        user_id=user_id,
        message=message,
        is_bot=is_bot
    )
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    return new_message
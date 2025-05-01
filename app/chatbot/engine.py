from sympy import false

from app.db.crud import save_message
from app.db.models import User
from sqlalchemy.orm import Session


def get_similar_response(user_input: str, user: User, conversation_id: int, db: Session):
    """ Saves  user's and bot's message to the conversation history. """

    save_message(user.id, conversation_id, user_input, False, db)
    ai_response = "hello there"
    save_message(user.id, conversation_id, ai_response, True, db)
    return ai_response
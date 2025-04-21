from sqlalchemy.orm import Session
from app.auth.utilits import verify_password
from app.db.connection import SessionLocal
from app.db.models import User



def get_session_local():
    """Get a database session using the SessionLocal dependency."""
    """db is the object created from the class(variable) SessionLocal in order to talk to db"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user(db, username: str):
    """find user by username"""
    return db.query(User).filter(User.username == username).first()


def authenticate_user(db: Session, username: str, password: str):
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user
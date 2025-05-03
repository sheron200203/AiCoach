"""models.py : contains all the models/classes mapped to the db tables"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship

from app.db.connection import Base


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    full_name = Column(String(100), nullable=True)
    email = Column(String(50), unique=True, index=True)
    hashed_password = Column(String(255))
    disabled = Column(Boolean, default=False)

    messages = relationship("MessageHistory", back_populates="user")
    facts = relationship("UserFact", back_populates="user")
    preferences = relationship("UserPreference", back_populates="user")


class UserFact(Base):
    __tablename__ = "user_facts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    key = Column(String(50))
    value = Column(String(50))

    user = relationship("User", back_populates="facts")


class UserPreference(Base):
    __tablename__ = "user_preferences"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    category = Column(String(50))
    value = Column(String(50))
    sentiment = Column(String(10))

    user = relationship("User", back_populates="preferences")


class MessageHistory(Base):
    __tablename__ = "message_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    message = Column(Text, nullable=False)
    is_bot = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.now())

    user = relationship("User", back_populates="messages")
    conversation = relationship("Conversation", back_populates="messages")

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String(255), default="New Conversation")
    created_at = Column(DateTime, default=datetime.utcnow)

    messages = relationship("MessageHistory", back_populates="conversation")
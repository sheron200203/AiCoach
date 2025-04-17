from sqlalchemy import Column, Integer, String, Boolean
from app.db.connection import Base


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    full_name = Column(String(100), nullable=True)
    email = Column(String(50), unique=True, index=True)
    hashed_password = Column(String(255))
    disabled = Column(Boolean, default=False)
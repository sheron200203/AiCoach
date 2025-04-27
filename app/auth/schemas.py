
from pydantic import BaseModel #Pydantic is a Python library used for data validation and data parsing
from typing import Optional


"""structured, validate user input """
class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = False

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str
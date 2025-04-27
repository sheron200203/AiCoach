
from fastapi import Depends, HTTPException, status, APIRouter
from app.auth.dependencies import authenticate_user, get_session_local
from app.auth.schemas import User, Token
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.auth.utils import create_access_token

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@router.post("/token",response_model=Token)
async def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: Session = Depends(get_session_local)
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},

        )
    token = create_access_token(data={"sub": user.username})
    return{
     "access_token":token, "token_type":"bearer"
    }


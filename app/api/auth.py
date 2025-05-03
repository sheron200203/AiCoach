
from fastapi import  status, APIRouter, Depends, HTTPException, Response
from app.auth.dependencies import authenticate_user, get_session_local
from app.auth.schemas import Token
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.auth.utils import create_access_token, create_refresh_token

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)



"""login endpoint"""
@router.post("/token", response_model=Token)
async def login_for_access_token(
        response: Response,
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

    access_token = create_access_token(data={"sub": user.username})
    refresh_token = create_refresh_token(data={"sub": user.username})

    # Set refresh token as HttpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="none",         # or strict "lax"
        max_age=60 * 60 * 24 * 7
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token # for mobile clients
    }

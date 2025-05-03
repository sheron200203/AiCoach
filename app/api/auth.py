
from fastapi import Depends, HTTPException, status, APIRouter, Request, Depends, HTTPException, Body, Response
from starlette.responses import JSONResponse

from app.auth.dependencies import authenticate_user, get_current_user, get_session_local, get_user
from app.auth.schemas import User, Token
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.auth.utils import create_access_token, create_refresh_token, decode_token

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



@router.post("/refresh")
async def refresh_token(
    request: Request,
    db: Session = Depends(get_session_local),
    body: dict = Body(default={})
):
    """
    Refresh access token. Supports:
    - refresh token in cookie
    - Authorization header
    - JSON body
    """
    # 1. Try cookie
    refresh_token = request.cookies.get("refresh_token")

    # # 2. Try Authorization header //Todo decide if to remove since it may cause issues if access token is parsed from FE
    # if not refresh_token:
    #     auth_header = request.headers.get("Authorization")
    #     if auth_header and auth_header.startswith("Bearer "):
    #         refresh_token = auth_header.split(" ")[1]

    # 3. Try JSON body
    if not refresh_token:
        refresh_token = body.get("refresh_token")

    # 4. If no token found
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token provided")

    # 5. Decode token and validate user
    decoded_token = await decode_token(refresh_token, 'sub', type='refresh')
    if not decoded_token:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user = get_user(db, username=decoded_token)
    if not user:
        raise HTTPException(status_code=401, detail="User does not exist")

    # 6. Create new access token
    access_token = create_access_token(data={"sub": user.username})
    return JSONResponse({"token": access_token, "email": user.email}, status_code=200)

@router.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, Token, UserLogin, UserUpdate
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
)
from app.config import settings

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user."""
    # Check if email exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Check if username exists
    result = await db.execute(select(User).where(User.username == user_data.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already taken")

    user = User(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        hashed_password=get_password_hash(user_data.password),
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    """Login and get access token."""
    result = await db.execute(select(User).where(User.email == user_data.email))
    user = result.scalar_one_or_none()

    if not user or not user.hashed_password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Account is inactive")

    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return Token(access_token=access_token, user=user)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user profile."""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current user profile."""
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
    if user_update.preferred_language is not None:
        current_user.preferred_language = user_update.preferred_language
    if user_update.response_language is not None:
        current_user.response_language = user_update.response_language

    await db.flush()
    await db.refresh(current_user)
    return current_user


@router.get("/google")
async def google_auth():
    """Initiate Google OAuth flow."""
    from google_auth_oauthlib.flow import Flow

    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
            }
        },
        scopes=[
            "openid",
            "email",
            "profile",
            "https://www.googleapis.com/auth/gmail.modify",
        ],
    )
    flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
    )
    return {"auth_url": authorization_url, "state": state}


@router.get("/google/callback")
async def google_callback(code: str, state: str, db: AsyncSession = Depends(get_db)):
    """Handle Google OAuth callback."""
    try:
        from google_auth_oauthlib.flow import Flow
        from googleapiclient.discovery import build

        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
                }
            },
            scopes=["openid", "email", "profile", "https://www.googleapis.com/auth/gmail.modify"],
            state=state,
        )
        flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
        flow.fetch_token(code=code)
        credentials = flow.credentials

        # Get user info
        service = build("oauth2", "v2", credentials=credentials)
        user_info = service.userinfo().get().execute()

        # Find or create user
        result = await db.execute(select(User).where(User.google_id == user_info["id"]))
        user = result.scalar_one_or_none()

        if not user:
            result = await db.execute(select(User).where(User.email == user_info["email"]))
            user = result.scalar_one_or_none()

        if not user:
            user = User(
                email=user_info["email"],
                username=user_info["email"].split("@")[0],
                full_name=user_info.get("name"),
                avatar_url=user_info.get("picture"),
                google_id=user_info["id"],
                is_verified=True,
            )
            db.add(user)
            await db.flush()
        else:
            user.google_id = user_info["id"]
            user.avatar_url = user_info.get("picture")
            user.google_access_token = credentials.token
            user.google_refresh_token = credentials.refresh_token

        access_token = create_access_token(data={"sub": str(user.id)})
        return {
            "access_token": access_token,
            "redirect_url": f"{settings.FRONTEND_URL}/auth/callback?token={access_token}",
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"OAuth error: {str(e)}")

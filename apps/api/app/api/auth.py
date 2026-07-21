from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.rate_limit import RateLimitExceeded, auth_rate_limiter
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    MeResponse,
    ProfileUpdateRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.services.auth_service import (
    AuthError,
    login_user,
    logout_user,
    refresh_tokens,
    register_user,
    update_profile,
)

router = APIRouter(prefix="/auth", tags=["auth"])

RATE_LIMIT_MESSAGE = "Muitas tentativas. Aguarde um minuto e tente novamente."


def _client_host(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _check_rate_limit(
    bucket: str,
    identity: str,
    limit: int,
) -> None:
    try:
        auth_rate_limiter.check(bucket, identity, limit=limit, window_seconds=60)
    except RateLimitExceeded as exc:
        raise HTTPException(
            status_code=429,
            detail=RATE_LIMIT_MESSAGE,
            headers={"Retry-After": "60"},
        ) from exc


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(
    body: RegisterRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    _check_rate_limit("register", _client_host(request), limit=20)
    try:
        register_user(db, body.name, body.email, body.password)
        access, refresh, _ = login_user(db, body.email, body.password)
    except AuthError as e:
        from fastapi import HTTPException

        raise HTTPException(status_code=e.status_code, detail=e.message)
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/login", response_model=TokenResponse)
def login(
    body: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    identity = f"{_client_host(request)}:{body.email}"
    _check_rate_limit("login", identity, limit=5)
    try:
        access, refresh, _ = login_user(db, body.email, body.password)
    except AuthError as e:
        from fastapi import HTTPException

        raise HTTPException(status_code=e.status_code, detail=e.message)
    auth_rate_limiter.reset("login", identity)
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    body: RefreshRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    _check_rate_limit("refresh", _client_host(request), limit=15)
    try:
        access, refresh = refresh_tokens(db, body.refresh_token)
    except AuthError as e:
        from fastapi import HTTPException

        raise HTTPException(status_code=e.status_code, detail=e.message)
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/logout", status_code=204)
def logout(
    body: RefreshRequest | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    token = body.refresh_token if body else None
    logout_user(db, current_user.id, token)
    return None


@router.get("/me", response_model=MeResponse)
def me(current_user: User = Depends(get_current_user)):
    return MeResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        phone=current_user.phone,
        avatar_data_url=current_user.avatar_data_url,
    )


@router.patch("/me", response_model=MeResponse)
def update_me(
    body: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = update_profile(
        db,
        current_user,
        body.model_dump(exclude_unset=True),
    )
    return MeResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        phone=user.phone,
        avatar_data_url=user.avatar_data_url,
    )

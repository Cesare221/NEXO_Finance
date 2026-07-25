from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.config import settings
from app.core.rate_limit import RateLimitExceeded, RateLimitUnavailable, auth_rate_limiter
from app.core.security import fingerprint_token
from app.models.user import User
from app.schemas.account_security import RegistrationResponse
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    DeleteAccountRequest,
    MeResponse,
    ProfileUpdateRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserSessionResponse,
)
from app.services.account_security_service import request_email_verification_for_user
from app.services.auth_service import (
    AuthError,
    delete_user_account,
    export_user_data,
    list_active_sessions,
    login_user,
    logout_user,
    refresh_tokens,
    register_user,
    revoke_user_session,
    update_profile,
)

router = APIRouter(prefix="/auth", tags=["auth"])

RATE_LIMIT_MESSAGE = "Muitas tentativas. Aguarde um minuto e tente novamente."


def _client_host(request: Request) -> str:
    direct_host = request.client.host if request.client else "unknown"
    if direct_host in settings.proxy_ips:
        forwarded = request.headers.get("x-forwarded-for", "")
        candidate = forwarded.split(",", 1)[0].strip()
        if candidate:
            return candidate
    return direct_host


def _device_name(request: Request) -> str | None:
    agent = request.headers.get("user-agent", "").casefold()
    if not agent or "undici" in agent or "node" in agent:
        return None
    browser = "Navegador"
    if "edg/" in agent:
        browser = "Edge"
    elif "chrome/" in agent:
        browser = "Chrome"
    elif "firefox/" in agent:
        browser = "Firefox"
    elif "safari/" in agent:
        browser = "Safari"
    platform = "dispositivo"
    if "windows" in agent:
        platform = "Windows"
    elif "android" in agent:
        platform = "Android"
    elif "iphone" in agent or "ipad" in agent:
        platform = "iPhone ou iPad"
    elif "mac os" in agent:
        platform = "macOS"
    elif "linux" in agent:
        platform = "Linux"
    return f"{browser} em {platform}"


def _request_context(request: Request) -> tuple[str | None, str]:
    host = _client_host(request)
    return _device_name(request), fingerprint_token(f"{settings.secret_key}:{host}")


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
            headers={"Retry-After": str(exc.retry_after)},
        ) from exc
    except RateLimitUnavailable as exc:
        raise HTTPException(
            status_code=503,
            detail="Protecao temporariamente indisponivel. Tente novamente em instantes.",
            headers={"Retry-After": "30"},
        ) from exc


@router.post("/register", response_model=RegistrationResponse, status_code=201)
def register(
    body: RegisterRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    _check_rate_limit("register", _client_host(request), limit=20)
    if settings.environment.lower() == "production" and not body.privacy_accepted:
        raise HTTPException(
            status_code=422,
            detail="Voce precisa aceitar o Aviso de Privacidade para criar a conta.",
        )
    try:
        user = register_user(
            db,
            body.name,
            body.email,
            body.password,
            body.privacy_accepted,
            body.ai_data_processing_consent,
        )
        _, ip_hash = _request_context(request)
        request_email_verification_for_user(db, user, ip_hash)
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    return RegistrationResponse(status="verification_required", email=user.email)


@router.post("/login", response_model=LoginResponse)
def login(
    body: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    identity = f"{_client_host(request)}:{body.email}"
    _check_rate_limit("login", identity, limit=5)
    try:
        outcome = login_user(db, body.email, body.password, *_request_context(request))
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    auth_rate_limiter.reset("login", identity)
    return LoginResponse(
        status=outcome.status,
        access_token=outcome.access_token,
        refresh_token=outcome.refresh_token,
        token_type="bearer" if outcome.access_token else None,
        challenge_token=outcome.challenge_token,
        email=outcome.user.email if outcome.status == "email_verification_required" else None,
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    body: RefreshRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    _check_rate_limit("refresh", _client_host(request), limit=15)
    try:
        access, refresh = refresh_tokens(db, body.refresh_token, *_request_context(request))
    except AuthError as e:
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
        theme_preference=current_user.theme_preference,
        privacy_policy_version=current_user.privacy_policy_version,
        privacy_accepted_at=(
            current_user.privacy_accepted_at.isoformat()
            if current_user.privacy_accepted_at else None
        ),
        ai_data_processing_consent=current_user.ai_data_processing_consent,
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
        theme_preference=user.theme_preference,
        privacy_policy_version=user.privacy_policy_version,
        privacy_accepted_at=(user.privacy_accepted_at.isoformat() if user.privacy_accepted_at else None),
        ai_data_processing_consent=user.ai_data_processing_consent,
    )


@router.get("/me/export")
def export_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_rate_limit("privacy-export", str(current_user.id), limit=3)
    response = JSONResponse(export_user_data(db, current_user))
    response.headers["Cache-Control"] = "no-store"
    response.headers["Content-Disposition"] = 'attachment; filename="nexo-meus-dados.json"'
    return response


@router.delete("/me", status_code=204)
def delete_me(
    body: DeleteAccountRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_rate_limit("privacy-delete", str(current_user.id), limit=3)
    try:
        delete_user_account(db, current_user, body.password)
    except AuthError as error:
        raise HTTPException(status_code=error.status_code, detail=error.message) from error
    return Response(status_code=204)


@router.get("/sessions", response_model=list[UserSessionResponse])
def sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_active_sessions(db, current_user.id)


@router.delete("/sessions/{session_id}", status_code=204)
def revoke_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_rate_limit("session-revoke", str(current_user.id), limit=10)
    if not revoke_user_session(db, current_user.id, session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    return Response(status_code=204)

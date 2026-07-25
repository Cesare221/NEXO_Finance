from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.rate_limit import RateLimitExceeded, RateLimitUnavailable, auth_rate_limiter
from app.core.security import fingerprint_token
from app.models.user import User
from app.schemas.account_security import (
    EmailRequest,
    MfaChallengeRequest,
    MfaConfirmRequest,
    MfaConfirmResponse,
    MfaDisableRequest,
    MfaEnrollResponse,
    MfaStatusResponse,
    MfaStepUpRequest,
    PasswordResetConfirmation,
    TokenConfirmation,
)
from app.schemas.auth import TokenResponse
from app.services.account_security_service import (
    AccountSecurityError,
    confirm_email_verification,
    confirm_password_reset,
    request_email_verification,
    request_password_reset,
)
from app.services.mfa_service import (
    MfaError,
    complete_mfa_challenge,
    confirm_totp_enrollment,
    disable_totp,
    get_mfa_status,
    regenerate_recovery_codes,
    start_totp_enrollment,
)

router = APIRouter(prefix="/auth", tags=["account-security"])

RATE_LIMIT_MESSAGE = "Muitas tentativas. Aguarde um minuto e tente novamente."


def _client_host(request: Request) -> str:
    direct_host = request.client.host if request.client else "unknown"
    if direct_host in settings.proxy_ips:
        forwarded = request.headers.get("x-forwarded-for", "")
        candidate = forwarded.split(",", 1)[0].strip()
        if candidate:
            return candidate
    return direct_host


def _request_context(request: Request) -> tuple[str | None, str]:
    host = _client_host(request)
    return _device_name(request), fingerprint_token(f"{settings.secret_key}:{host}")


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


def _check_rate_limit(bucket: str, identity: str, limit: int, window_seconds: int = 60) -> None:
    try:
        auth_rate_limiter.check(bucket, identity, limit=limit, window_seconds=window_seconds)
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


@router.post("/email-verification/request", status_code=202)
def request_email_verification_endpoint(
    body: EmailRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    identity = f"{_client_host(request)}:{body.email}"
    _check_rate_limit("email-verify-request", identity, limit=3)
    _, ip_hash = _request_context(request)
    request_email_verification(db, body.email, ip_hash)
    return JSONResponse(
        status_code=202,
        content={"message": "Se o e-mail estiver cadastrado e pendente de verificacao, as instrucoes foram enviadas."},
    )


@router.post("/email-verification/confirm")
def confirm_email_verification_endpoint(
    body: TokenConfirmation,
    request: Request,
    db: Session = Depends(get_db),
):
    _check_rate_limit("email-verify-confirm", _client_host(request), limit=10)
    try:
        confirm_email_verification(db, body.token)
    except AccountSecurityError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return {"message": "E-mail verificado com sucesso."}


@router.post("/password-reset/request", status_code=202)
def request_password_reset_endpoint(
    body: EmailRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    identity = f"{_client_host(request)}:{body.email}"
    _check_rate_limit("password-reset-request", identity, limit=3)
    _, ip_hash = _request_context(request)
    request_password_reset(db, body.email, ip_hash)
    return JSONResponse(
        status_code=202,
        content={"message": "Se o e-mail estiver cadastrado, as instrucoes de redefinicao foram enviadas."},
    )


@router.post("/password-reset/confirm")
def confirm_password_reset_endpoint(
    body: PasswordResetConfirmation,
    request: Request,
    db: Session = Depends(get_db),
):
    _check_rate_limit("password-reset-confirm", _client_host(request), limit=5)
    try:
        confirm_password_reset(db, body.token, body.new_password)
    except AccountSecurityError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return {"message": "Senha redefinida com sucesso."}


@router.get("/mfa/status", response_model=MfaStatusResponse)
def get_mfa_status_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    enabled, activated_at = get_mfa_status(db, current_user.id)
    return MfaStatusResponse(enabled=enabled, activated_at=activated_at)


@router.post("/mfa/enroll", response_model=MfaEnrollResponse)
def mfa_enroll_endpoint(
    body: MfaStepUpRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        secret, otpauth_uri = start_totp_enrollment(db, current_user, body.password)
    except MfaError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return MfaEnrollResponse(secret=secret, otpauth_uri=otpauth_uri)


@router.post("/mfa/confirm", response_model=MfaConfirmResponse)
def mfa_confirm_endpoint(
    body: MfaConfirmRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        codes = confirm_totp_enrollment(db, current_user, body.code)
    except MfaError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return MfaConfirmResponse(recovery_codes=codes)


@router.post("/mfa/challenge", response_model=TokenResponse)
def mfa_challenge_endpoint(
    body: MfaChallengeRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    _check_rate_limit("mfa-challenge", _client_host(request), limit=10)
    device_name, ip_hash = _request_context(request)
    try:
        access_token, refresh_token, _ = complete_mfa_challenge(
            db, body.challenge_token, body.code, device_name, ip_hash
        )
    except MfaError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/mfa/recovery-codes", response_model=MfaConfirmResponse)
def mfa_regenerate_recovery_codes_endpoint(
    body: MfaStepUpRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        codes = regenerate_recovery_codes(db, current_user, body.password)
    except MfaError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return MfaConfirmResponse(recovery_codes=codes)


@router.delete("/mfa")
def mfa_disable_endpoint(
    body: MfaDisableRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        disable_totp(db, current_user, body.password, body.code)
    except MfaError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return {"message": "MFA desativado com sucesso."}

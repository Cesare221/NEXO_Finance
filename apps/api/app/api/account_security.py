from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.rate_limit import RateLimitExceeded, RateLimitUnavailable, auth_rate_limiter
from app.core.security import fingerprint_token
from app.schemas.account_security import (
    EmailRequest,
    PasswordResetConfirmation,
    TokenConfirmation,
)
from app.services.account_security_service import (
    AccountSecurityError,
    confirm_email_verification,
    confirm_password_reset,
    request_email_verification,
    request_password_reset,
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


def _request_context(request: Request) -> str:
    host = _client_host(request)
    return fingerprint_token(f"{settings.secret_key}:{host}")


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
    request_email_verification(db, body.email, _request_context(request))
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
    request_password_reset(db, body.email, _request_context(request))
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

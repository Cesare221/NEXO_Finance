import logging
import time
from contextlib import asynccontextmanager
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.account_security import router as account_security_router
from app.api.auth import router as auth_router
from app.api.assistant import router as assistant_router
from app.api.financial import router as financial_router
from app.api.health import router as health_router
from app.core.config import settings
from app.core.logging_config import _request_id_var, configure_logging
from app.core.observability import init_observability
from app.core.rate_limit import RateLimitExceeded, RateLimitUnavailable, auth_rate_limiter
from app.core.security import fingerprint_token

logger = logging.getLogger("nexo.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(environment=settings.environment)
    settings.validate_runtime()
    init_observability()
    yield


is_production = settings.environment.lower() == "production"
app = FastAPI(
    title="Nexo API",
    version="0.1.0",
    lifespan=lifespan,
    docs_url=None if is_production else "/docs",
    redoc_url=None if is_production else "/redoc",
    openapi_url=None if is_production else "/openapi.json",
)

if is_production:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.host_allowlist)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def api_security_headers(request: Request, call_next):
    request_id = request.headers.get("x-request-id")
    try:
        request_id = str(uuid.UUID(request_id)) if request_id else str(uuid.uuid4())
    except ValueError:
        request_id = str(uuid.uuid4())

    _request_id_var.set(request_id)
    start_time = time.monotonic()

    content_length = request.headers.get("content-length")
    try:
        body_size = int(content_length) if content_length else 0
    except ValueError:
        body_size = 1_000_001
    if body_size > 1_000_000:
        return JSONResponse(
            {"detail": "Request body is too large"},
            status_code=413,
            headers={"X-Request-ID": request_id, "Cache-Control": "no-store"},
        )

    if request.method in {"POST", "PUT", "PATCH", "DELETE"} and request.url.path.startswith("/financial"):
        authorization = request.headers.get("authorization", "")
        identity = fingerprint_token(authorization) if authorization else (request.client.host if request.client else "unknown")
        try:
            auth_rate_limiter.check("financial-write", identity, limit=60, window_seconds=60)
        except RateLimitExceeded as error:
            return JSONResponse(
                {"detail": "Muitas operações em pouco tempo. Aguarde e tente novamente."},
                status_code=429,
                headers={"Retry-After": str(error.retry_after), "X-Request-ID": request_id},
            )
        except RateLimitUnavailable:
            return JSONResponse(
                {"detail": "Proteção temporariamente indisponível."},
                status_code=503,
                headers={"Retry-After": "30", "X-Request-ID": request_id},
            )

    response = await call_next(request)
    duration_ms = round((time.monotonic() - start_time) * 1000, 1)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if is_production:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    logger.info(
        "request.complete",
        extra={
            "request_id": request_id,
            "method": request.method,
            "route": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        },
    )
    return response

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(account_security_router)
app.include_router(financial_router)
app.include_router(assistant_router)

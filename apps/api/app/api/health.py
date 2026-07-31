from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check():
    return {"status": "ok"}


@router.get("/ready")
def readiness_check(db: Session = Depends(get_db)):
    checks: dict[str, str] = {}

    # Database check
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "not_ready", "checks": {"database": "unavailable"}},
            headers={"Retry-After": "5"},
        )

    # Redis check (production only)
    if settings.environment.lower() == "production" and settings.redis_url:
        try:
            import redis as _redis
            client = _redis.from_url(settings.redis_url, socket_timeout=3)
            client.ping()
            client.close()
            checks["redis"] = "ok"
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"status": "not_ready", "checks": {**checks, "redis": "unavailable"}},
                headers={"Retry-After": "5"},
            )

    return {"status": "ready", "checks": checks}


@router.get("/debug/sentry-test", include_in_schema=False)
def sentry_test(token: str = ""):
    if settings.environment.lower() == "production":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    expected_token = getattr(settings, "sentry_test_token", "")
    if not expected_token:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    if token != expected_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    raise RuntimeError("Sentry API test event")

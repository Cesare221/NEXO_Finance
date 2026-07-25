"""Maintenance CLI for purging expired security records.

Usage:
    python -m app.maintenance purge-expired-security-records
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone

from sqlalchemy import delete

from app.core.database import SessionLocal
from app.models.account_action_token import AccountActionToken
from app.models.mfa_challenge import MfaChallenge


def purge_expired_security_records(session_factory=SessionLocal) -> dict[str, int]:
    """Delete expired and consumed security records older than 30 days.

    Returns aggregate counts of deleted records.
    """
    cutoff = datetime.now(timezone.utc)
    thirty_days_ago = datetime(
        cutoff.year, cutoff.month, cutoff.day,
        tzinfo=timezone.utc,
    )

    with session_factory() as db:
        # Purge expired account action tokens
        token_result = db.execute(
            delete(AccountActionToken).where(
                AccountActionToken.expires_at < thirty_days_ago
            )
        )

        # Purge expired and consumed MFA challenges
        challenge_result = db.execute(
            delete(MfaChallenge).where(
                MfaChallenge.expires_at < thirty_days_ago
            )
        )

        db.commit()

    return {
        "account_action_tokens_deleted": token_result.rowcount,
        "mfa_challenges_deleted": challenge_result.rowcount,
        "status": "ok",
    }


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] != "purge-expired-security-records":
        print("Usage: python -m app.maintenance purge-expired-security-records", file=sys.stderr)
        sys.exit(1)

    result = purge_expired_security_records()
    print(json.dumps(result))


if __name__ == "__main__":
    main()

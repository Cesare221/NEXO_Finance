#!/usr/bin/env python
"""
Production smoke test script.
Validates health, readiness, web headers, and optional authenticated flows.
"""
import argparse
import asyncio
import json
import sys
import time
from typing import Optional, Tuple

import httpx


async def check_health(api_url: str, client: httpx.AsyncClient) -> dict:
    """Check /health endpoint."""
    try:
        start = time.perf_counter()
        response = await client.get(f"{api_url}/health")
        response.raise_for_status()
        duration_ms = (time.perf_counter() - start) * 1000
        return {"check": "health", "status": "pass", "duration_ms": duration_ms}
    except httpx.HTTPStatusError as e:
        return {"check": "health", "status": "fail", "error": f"HTTP {e.response.status_code}"}
    except Exception as e:
        return {"check": "health", "status": "fail", "error": str(e)}


async def check_readiness(api_url: str, client: httpx.AsyncClient) -> dict:
    """Check /ready endpoint."""
    try:
        start = time.perf_counter()
        response = await client.get(f"{api_url}/ready")
        response.raise_for_status()
        data = response.json()
        duration_ms = (time.perf_counter() - start) * 1000
        if data.get("status") != "ready":
            return {"check": "readiness", "status": "fail", "error": f"Not ready: {data}"}
        return {"check": "readiness", "status": "pass", "duration_ms": duration_ms}
    except httpx.HTTPStatusError as e:
        return {"check": "readiness", "status": "fail", "error": f"HTTP {e.response.status_code}"}
    except Exception as e:
        return {"check": "readiness", "status": "fail", "error": str(e)}


async def check_web_headers(web_url: str, client: httpx.AsyncClient) -> dict:
    """Check web security headers (CSP, HSTS)."""
    try:
        response = await client.get(web_url)
        response.raise_for_status()

        csp = response.headers.get("content-security-policy")
        hsts = response.headers.get("strict-transport-security")

        if not csp:
            return {"check": "web_headers", "status": "fail", "error": "Missing Content-Security-Policy header"}

        if not hsts:
            return {"check": "web_headers", "status": "fail", "error": "Missing HSTS header"}

        return {"check": "web_headers", "status": "pass"}
    except httpx.HTTPStatusError as e:
        return {"check": "web_headers", "status": "fail", "error": f"HTTP {e.response.status_code}"}
    except Exception as e:
        return {"check": "web_headers", "status": "fail", "error": str(e)}


async def login(
    api_url: str, client: httpx.AsyncClient, email: str, password: str
) -> Tuple[Optional[str], Optional[str]]:
    """Login and return (access_token, refresh_token) or (None, None) if MFA/verification required."""
    response = await client.post(
        f"{api_url}/auth/login",
        json={"email": email, "password": password},
    )
    response.raise_for_status()
    data = response.json()
    status = data.get("status")

    if status == "authenticated":
        return data["access_token"], data["refresh_token"]
    elif status == "mfa_required":
        return None, None
    elif status == "email_verification_required":
        return None, None
    else:
        raise RuntimeError(f"Unexpected login status: {status}")


async def complete_mfa_challenge(
    api_url: str, client: httpx.AsyncClient, challenge_token: str, code: str
) -> Tuple[str, str]:
    """Complete MFA challenge and return tokens."""
    response = await client.post(
        f"{api_url}/auth/mfa/challenge",
        json={"challenge_token": challenge_token, "code": code},
    )
    response.raise_for_status()
    data = response.json()
    if data.get("status") != "authenticated":
        raise RuntimeError("MFA challenge failed")
    return data["access_token"], data["refresh_token"]


async def refresh_token(
    api_url: str, client: httpx.AsyncClient, refresh_token: str
) -> Tuple[str, str]:
    """Rotate refresh token."""
    response = await client.post(
        f"{api_url}/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    response.raise_for_status()
    data = response.json()
    return data["access_token"], data["refresh_token"]


async def get_current_user(
    api_url: str, client: httpx.AsyncClient, access_token: str
) -> dict:
    """Get current user info."""
    response = await client.get(
        f"{api_url}/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    response.raise_for_status()
    return response.json()


async def read_dashboard(
    api_url: str, client: httpx.AsyncClient, access_token: str
) -> dict:
    """Read financial dashboard."""
    response = await client.get(
        f"{api_url}/financial/dashboard",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    response.raise_for_status()
    return response.json()


async def logout(
    api_url: str, client: httpx.AsyncClient, access_token: str, refresh_token: str
) -> None:
    """Logout and revoke tokens."""
    response = await client.post(
        f"{api_url}/auth/logout",
        json={"refresh_token": refresh_token},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    response.raise_for_status()


async def run_authenticated_checks(
    api_url: str,
    web_url: str,
    email: str,
    password: str,
    totp_secret: Optional[str],
    client: httpx.AsyncClient,
) -> list[dict]:
    """Run authenticated smoke checks using the provided client."""
    results = []

    # Login
    access_token, refresh_token_str = await login(api_url, client, email, password)

    if access_token is None:
        # Check why login didn't return tokens
        login_response = await client.post(
            f"{api_url}/auth/login",
            json={"email": email, "password": password},
        )
        login_response.raise_for_status()
        login_data = login_response.json()

        if login_data.get("status") == "mfa_required":
            if not totp_secret:
                results.append({"check": "mfa", "status": "skip", "reason": "No TOTP secret provided"})
                return results
            import pyotp
            code = pyotp.TOTP(totp_secret).now()
            access_token, refresh_token_str = await complete_mfa_challenge(
                api_url, client, login_data["challenge_token"], code
            )
            results.append({"check": "mfa", "status": "pass"})
        elif login_data.get("status") == "email_verification_required":
            results.append({"check": "email_verification", "status": "skip", "reason": "Email not verified"})
            return results
        else:
            raise RuntimeError(f"Unexpected login status: {login_data.get('status')}")

    results.append({"check": "login", "status": "pass"})

    # Refresh rotation
    access_token, refresh_token_str = await refresh_token(api_url, client, refresh_token_str)
    results.append({"check": "refresh", "status": "pass"})

    # /auth/me
    await get_current_user(api_url, client, access_token)
    results.append({"check": "auth_me", "status": "pass"})

    # Dashboard read
    await read_dashboard(api_url, client, access_token)
    results.append({"check": "dashboard", "status": "pass"})

    # Logout
    await logout(api_url, client, access_token, refresh_token_str)
    results.append({"check": "logout", "status": "pass"})

    return results


async def run_smoke_checks(
    api_url: str,
    web_url: str,
    email: Optional[str],
    password: Optional[str],
    totp_secret: Optional[str],
    allow_http_localhost: bool = False,
) -> list[dict]:
    """Run all smoke checks."""
    results = []

    # Validate HTTPS in production
    if not allow_http_localhost:
        for url, name in [(api_url, "API"), (web_url, "Web")]:
            if not url.startswith("https://"):
                results.append({
                    "check": f"{name.lower()}_https",
                    "status": "fail",
                    "error": f"{name} URL must be HTTPS in production"
                })
                return results

    async with httpx.AsyncClient(timeout=10.0, follow_redirects=False) as client:
        # Health
        results.append(await check_health(api_url, client))

        # Readiness
        results.append(await check_readiness(api_url, client))

        # Web headers
        results.append(await check_web_headers(web_url, client))

        # Authenticated checks
        if email and password:
            try:
                auth_results = await run_authenticated_checks(
                    api_url, web_url, email, password, totp_secret, client
                )
                results.extend(auth_results)
            except Exception as e:
                results.append({"check": "authenticated", "status": "fail", "error": str(e)})
        else:
            results.append({"check": "authenticated", "status": "skip", "reason": "No credentials provided"})

    return results


def print_results(results: list[dict]) -> int:
    """Print results as JSON lines and return exit code."""
    exit_code = 0
    for result in results:
        print(json.dumps(result, ensure_ascii=False))
        if result.get("status") == "fail":
            exit_code = 1
    return exit_code


def main() -> int:
    parser = argparse.ArgumentParser(description="Production smoke tests")
    parser.add_argument("--api-url", required=True, help="API base URL")
    parser.add_argument("--web-url", required=True, help="Web base URL")
    parser.add_argument("--email", help="Test user email")
    parser.add_argument("--password", help="Test user password")
    parser.add_argument("--totp-secret", help="TOTP secret for MFA")
    parser.add_argument("--allow-http-localhost", action="store_true",
                        help="Allow HTTP for localhost testing")
    args = parser.parse_args()

    results = asyncio.run(run_smoke_checks(
        api_url=args.api_url,
        web_url=args.web_url,
        email=args.email,
        password=args.password,
        totp_secret=args.totp_secret,
        allow_http_localhost=args.allow_http_localhost,
    ))

    return print_results(results)


if __name__ == "__main__":
    sys.exit(main())
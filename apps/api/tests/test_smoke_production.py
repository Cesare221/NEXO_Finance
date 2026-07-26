"""
Smoke production tests with HTTPX mock transport.
Tests verify the smoke script behavior without making real HTTP calls.
"""
import json
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
import pytest_asyncio

# Add scripts to path
sys.path.insert(0, "scripts")

from scripts.smoke_production import (
    run_smoke_checks,
    check_health,
    check_readiness,
    check_web_headers,
    run_authenticated_checks,
    login,
    refresh_token,
    get_current_user,
    read_dashboard,
    logout,
    print_results,
    main,
)


class MockAsyncClient:
    """Mock HTTPX AsyncClient for testing."""

    def __init__(self, responses=None):
        self.responses = responses or {}
        self.requests = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    def _make_response(self, method: str, url: str, key: tuple, default: httpx.Response) -> httpx.Response:
        """Create response with proper request set."""
        if key in self.responses:
            resp = self.responses[key]
        else:
            resp = default
        # Create a new response with request set for raise_for_status()
        request = httpx.Request(method, url)
        # Handle case where resp has no content (e.g., 204 No Content)
        json_data = None
        if hasattr(resp, 'json') and getattr(resp, 'content', None):
            try:
                json_data = resp.json()
            except Exception:
                json_data = None
        return httpx.Response(
            resp.status_code,
            json=json_data,
            headers=resp.headers,
            request=request,
        )

    async def get(self, url, *args, **kwargs):
        self.requests.append({"method": "GET", "url": url, "kwargs": kwargs})
        return self._make_response("GET", url, ("GET", url), httpx.Response(404, json={"detail": "Not found"}))

    async def post(self, url, *args, **kwargs):
        self.requests.append({"method": "POST", "url": url, "kwargs": kwargs})
        return self._make_response("POST", url, ("POST", url), httpx.Response(404, json={"detail": "Not found"}))

    async def delete(self, url, *args, **kwargs):
        self.requests.append({"method": "DELETE", "url": url, "kwargs": kwargs})
        return self._make_response("DELETE", url, ("DELETE", url), httpx.Response(404, json={"detail": "Not found"}))


def make_response(status_code: int, json_data: dict = None, headers: dict = None):
    """Create an httpx Response (used as template for mock)."""
    return httpx.Response(status_code, json=json_data, headers=headers)


@pytest.fixture
def mock_client():
    return MockAsyncClient()


class TestHealthChecks:
    """Test health and readiness endpoints."""

    @pytest.mark.asyncio
    async def test_check_health_success(self, mock_client):
        mock_client.responses[("GET", "https://api.example.com/health")] = make_response(
            200, {"status": "ok"}
        )
        result = await check_health("https://api.example.com", mock_client)
        assert result == {"check": "health", "status": "pass", "duration_ms": pytest.approx(0, abs=1000)}

    @pytest.mark.asyncio
    async def test_check_health_failure(self, mock_client):
        mock_client.responses[("GET", "https://api.example.com/health")] = make_response(
            503, {"status": "degraded"}
        )
        result = await check_health("https://api.example.com", mock_client)
        assert result["check"] == "health"
        assert result["status"] == "fail"

    @pytest.mark.asyncio
    async def test_check_readiness_success(self, mock_client):
        mock_client.responses[("GET", "https://api.example.com/ready")] = make_response(
            200, {"status": "ready", "checks": {"database": "ok", "redis": "ok"}}
        )
        result = await check_readiness("https://api.example.com", mock_client)
        assert result == {"check": "readiness", "status": "pass", "duration_ms": pytest.approx(0, abs=1000)}

    @pytest.mark.asyncio
    async def test_check_readiness_failure(self, mock_client):
        mock_client.responses[("GET", "https://api.example.com/ready")] = make_response(
            503, {"detail": {"status": "not_ready", "checks": {"database": "unavailable"}}}
        )
        result = await check_readiness("https://api.example.com", mock_client)
        assert result["check"] == "readiness"
        assert result["status"] == "fail"


class TestWebHeaders:
    """Test web CSP and HSTS headers."""

    @pytest.mark.asyncio
    async def test_check_web_headers_success(self, mock_client):
        mock_client.responses[("GET", "https://app.example.com")] = make_response(
            200,
            {},
            headers={
                "Content-Security-Policy": "default-src 'self'",
                "Strict-Transport-Security": "max-age=31536000",
            }
        )
        result = await check_web_headers("https://app.example.com", mock_client)
        assert result == {"check": "web_headers", "status": "pass"}

    @pytest.mark.asyncio
    async def test_check_web_headers_missing_csp(self, mock_client):
        mock_client.responses[("GET", "https://app.example.com")] = make_response(
            200,
            {},
            headers={"Strict-Transport-Security": "max-age=31536000"}
        )
        result = await check_web_headers("https://app.example.com", mock_client)
        assert result["check"] == "web_headers"
        assert result["status"] == "fail"
        assert "Content-Security-Policy" in result["error"]

    @pytest.mark.asyncio
    async def test_check_web_headers_missing_hsts(self, mock_client):
        mock_client.responses[("GET", "https://app.example.com")] = make_response(
            200,
            {},
            headers={"Content-Security-Policy": "default-src 'self'"}
        )
        result = await check_web_headers("https://app.example.com", mock_client)
        assert result["check"] == "web_headers"
        assert result["status"] == "fail"
        assert "HSTS" in result["error"]


class TestAuthenticatedChecks:
    """Test authenticated smoke checks."""

    @pytest.mark.asyncio
    async def test_login_success(self, mock_client):
        mock_client.responses[("POST", "https://api.example.com/auth/login")] = make_response(
            200,
            {
                "status": "authenticated",
                "access_token": "access-123",
                "refresh_token": "refresh-123",
                "token_type": "bearer",
            }
        )
        access, refresh = await login("https://api.example.com", mock_client, "user@example.com", "password")
        assert access == "access-123"
        assert refresh == "refresh-123"

    @pytest.mark.asyncio
    async def test_login_mfa_required(self, mock_client):
        mock_client.responses[("POST", "https://api.example.com/auth/login")] = make_response(
            200,
            {
                "status": "mfa_required",
                "challenge_token": "challenge-123",
                "email": "user@example.com",
            }
        )
        access, refresh = await login("https://api.example.com", mock_client, "user@example.com", "password")
        # Should return None for both when MFA required
        assert access is None
        assert refresh is None

    @pytest.mark.asyncio
    async def test_login_email_verification_required(self, mock_client):
        mock_client.responses[("POST", "https://api.example.com/auth/login")] = make_response(
            200,
            {
                "status": "email_verification_required",
                "email": "user@example.com",
            }
        )
        access, refresh = await login("https://api.example.com", mock_client, "user@example.com", "password")
        assert access is None
        assert refresh is None

    @pytest.mark.asyncio
    async def test_refresh_token_rotation(self, mock_client):
        mock_client.responses[("POST", "https://api.example.com/auth/refresh")] = make_response(
            200,
            {
                "access_token": "new-access-456",
                "refresh_token": "new-refresh-456",
                "token_type": "bearer",
            }
        )
        access, refresh = await refresh_token("https://api.example.com", mock_client, "old-refresh")
        assert access == "new-access-456"
        assert refresh == "new-refresh-456"

    @pytest.mark.asyncio
    async def test_get_current_user(self, mock_client):
        mock_client.responses[("GET", "https://api.example.com/auth/me")] = make_response(
            200,
            {"email": "user@example.com", "name": "Test User"}
        )
        result = await get_current_user("https://api.example.com", mock_client, "access-123")
        assert result["email"] == "user@example.com"

    @pytest.mark.asyncio
    async def test_read_dashboard(self, mock_client):
        mock_client.responses[("GET", "https://api.example.com/financial/dashboard")] = make_response(
            200,
            {"balance": 1000, "transactions": []}
        )
        result = await read_dashboard("https://api.example.com", mock_client, "access-123")
        assert result["balance"] == 1000

    @pytest.mark.asyncio
    async def test_logout(self, mock_client):
        mock_client.responses[("POST", "https://api.example.com/auth/logout")] = make_response(
            204,
        )
        await logout("https://api.example.com", mock_client, "access-123", "refresh-123")
        # Verify request was made with correct headers and body
        logout_req = mock_client.requests[-1]
        assert logout_req["method"] == "POST"
        assert logout_req["url"] == "https://api.example.com/auth/logout"
        assert "Authorization" in logout_req["kwargs"].get("headers", {})


class TestFullSmokeRun:
    """Test complete smoke check runs."""

    @pytest.mark.asyncio
    async def test_run_smoke_checks_public_only(self):
        """Test smoke checks without credentials (public only)."""
        client = MockAsyncClient()
        client.responses[("GET", "https://api.example.com/health")] = make_response(200, {"status": "ok"})
        client.responses[("GET", "https://api.example.com/ready")] = make_response(
            200, {"status": "ready", "checks": {"database": "ok"}}
        )
        client.responses[("GET", "https://app.example.com/")] = make_response(
            200, {}, headers={"Content-Security-Policy": "default-src 'self'", "Strict-Transport-Security": "max-age=31536000"}
        )

        with patch("scripts.smoke_production.httpx.AsyncClient", return_value=client):
            results = await run_smoke_checks(
                api_url="https://api.example.com",
                web_url="https://app.example.com",
                email=None,
                password=None,
                totp_secret=None,
                allow_http_localhost=False,
            )

        checks = [r["check"] for r in results]
        assert "health" in checks
        assert "readiness" in checks
        assert "web_headers" in checks
        assert "authenticated" in checks
        # Authenticated should be skipped
        auth_result = next(r for r in results if r["check"] == "authenticated")
        assert auth_result["status"] == "skip"

    @pytest.mark.asyncio
    async def test_run_smoke_checks_with_auth(self):
        """Test smoke checks with valid credentials."""
        client = MockAsyncClient()
        client.responses[("GET", "https://api.example.com/health")] = make_response(200, {"status": "ok"})
        client.responses[("GET", "https://api.example.com/ready")] = make_response(
            200, {"status": "ready", "checks": {"database": "ok"}}
        )
        client.responses[("GET", "https://app.example.com")] = make_response(
            200, {}, headers={"Content-Security-Policy": "default-src 'self'", "Strict-Transport-Security": "max-age=31536000"}
        )
        # Login
        client.responses[("POST", "https://api.example.com/auth/login")] = make_response(
            200, {"status": "authenticated", "access_token": "at", "refresh_token": "rt", "token_type": "bearer"}
        )
        # Refresh
        client.responses[("POST", "https://api.example.com/auth/refresh")] = make_response(
            200, {"access_token": "at2", "refresh_token": "rt2", "token_type": "bearer"}
        )
        # /auth/me
        client.responses[("GET", "https://api.example.com/auth/me")] = make_response(200, {"email": "u@e.com"})
        # Dashboard
        client.responses[("GET", "https://api.example.com/financial/dashboard")] = make_response(200, {"balance": 0})
        # Logout
        client.responses[("POST", "https://api.example.com/auth/logout")] = make_response(204)

        with patch("scripts.smoke_production.httpx.AsyncClient", return_value=client):
            results = await run_smoke_checks(
                api_url="https://api.example.com",
                web_url="https://app.example.com",
                email="user@example.com",
                password="password",
                totp_secret=None,
                allow_http_localhost=False,
            )

        checks = [r["check"] for r in results]
        assert "health" in checks
        assert "readiness" in checks
        assert "web_headers" in checks
        assert "login" in checks
        assert "refresh" in checks
        assert "auth_me" in checks
        assert "dashboard" in checks
        assert "logout" in checks
        # All should pass
        for r in results:
            assert r["status"] == "pass", f"Check {r['check']} failed: {r.get('error')}"

    @pytest.mark.asyncio
    async def test_run_smoke_checks_rejects_http_in_production(self):
        """Test that HTTP URLs are rejected in production mode."""
        client = MockAsyncClient()

        with patch("scripts.smoke_production.httpx.AsyncClient", return_value=client):
            results = await run_smoke_checks(
                api_url="http://api.example.com",
                web_url="https://app.example.com",
                email=None,
                password=None,
                totp_secret=None,
                allow_http_localhost=False,
            )

        assert results[0]["check"] == "api_https"
        assert results[0]["status"] == "fail"
        assert "HTTPS" in results[0]["error"]


class TestNoFinancialMutations:
    """Ensure smoke script never calls financial mutation endpoints."""

    @pytest.mark.asyncio
    async def test_no_financial_mutation_calls(self):
        """Verify the script never POSTs/PUTs/DELETEs to financial endpoints."""
        client = MockAsyncClient()
        client.responses[("GET", "https://api.example.com/health")] = make_response(200, {"status": "ok"})
        client.responses[("GET", "https://api.example.com/ready")] = make_response(
            200, {"status": "ready", "checks": {"database": "ok"}}
        )
        client.responses[("GET", "https://app.example.com/")] = make_response(
            200, {}, headers={"Content-Security-Policy": "default-src 'self'", "Strict-Transport-Security": "max-age=31536000"}
        )
        client.responses[("POST", "https://api.example.com/auth/login")] = make_response(
            200, {"status": "authenticated", "access_token": "at", "refresh_token": "rt", "token_type": "bearer"}
        )
        client.responses[("POST", "https://api.example.com/auth/refresh")] = make_response(
            200, {"access_token": "at2", "refresh_token": "rt2", "token_type": "bearer"}
        )
        client.responses[("GET", "https://api.example.com/auth/me")] = make_response(200, {"email": "u@e.com"})
        client.responses[("GET", "https://api.example.com/financial/dashboard")] = make_response(200, {"balance": 0})
        client.responses[("POST", "https://api.example.com/auth/logout")] = make_response(204)

        with patch("scripts.smoke_production.httpx.AsyncClient", return_value=client):
            await run_smoke_checks(
                api_url="https://api.example.com",
                web_url="https://app.example.com",
                email="user@example.com",
                password="password",
                totp_secret=None,
                allow_http_localhost=False,
            )

        # Check no financial mutation endpoints were called
        financial_mutations = [
            "POST /financial/transactions",
            "POST /financial/accounts",
            "PUT /financial/transactions",
            "DELETE /financial/transactions",
            "POST /financial/categories",
        ]

        for req in client.requests:
            url = req["url"]
            method = req["method"]
            # Should not call any financial mutation endpoints
            assert not any(mut in url for mut in ["/financial/transactions", "/financial/accounts", "/financial/categories"]) or method == "GET"


class TestPrintResults:
    """Test results printing."""

    def test_print_results_all_pass(self, capsys):
        results = [
            {"check": "health", "status": "pass"},
            {"check": "readiness", "status": "pass"},
        ]
        exit_code = print_results(results)
        captured = capsys.readouterr()
        assert exit_code == 0
        lines = captured.out.strip().split("\n")
        assert len(lines) == 2
        assert json.loads(lines[0])["check"] == "health"

    def test_print_results_one_fail(self, capsys):
        results = [
            {"check": "health", "status": "pass"},
            {"check": "readiness", "status": "fail", "error": "database down"},
        ]
        exit_code = print_results(results)
        assert exit_code == 1


class TestMain:
    """Test main entry point."""

    @patch("scripts.smoke_production.asyncio.run")
    @patch("scripts.smoke_production.print_results")
    @patch("scripts.smoke_production.run_smoke_checks")
    @patch("sys.argv", ["smoke_production.py", "--api-url", "https://api.example.com", "--web-url", "https://app.example.com"])
    def test_main(self, mock_run_smoke, mock_print, mock_asyncio_run):
        mock_run_smoke.return_value = [{"check": "health", "status": "pass"}]
        mock_print.return_value = 0
        mock_asyncio_run.side_effect = lambda coro: coro.__await__().__next__()

        with pytest.raises(StopIteration):
            main()

        # Verify args parsing
        assert mock_run_smoke.called


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
"""
Unit tests for the auth API — login, token verification, require_admin dependency.
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials


class TestAdminLogin:

    @pytest.mark.asyncio
    async def test_login_success(self, test_client):
        """Valid credentials return a JWT access_token."""
        with patch("app.api.auth.settings") as mock_settings:
            mock_settings.environment = "development"
            mock_settings.admin_email = "admin@test.com"
            mock_settings.admin_password = "testpassword123"
            mock_settings.nextauth_secret = "test-secret"

            response = await test_client.post(
                "/api/auth/login",
                json={"email": "admin@test.com", "password": "testpassword123"},
            )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 20

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, test_client):
        """Wrong password returns 401."""
        with patch("app.api.auth.settings") as mock_settings:
            mock_settings.environment = "development"
            mock_settings.admin_email = "admin@test.com"
            mock_settings.admin_password = "correctpassword"
            mock_settings.nextauth_secret = "test-secret"

            response = await test_client.post(
                "/api/auth/login",
                json={"email": "admin@test.com", "password": "wrongpassword"},
            )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_wrong_email(self, test_client):
        """Wrong email returns 401."""
        with patch("app.api.auth.settings") as mock_settings:
            mock_settings.environment = "development"
            mock_settings.admin_email = "admin@test.com"
            mock_settings.admin_password = "testpassword123"
            mock_settings.nextauth_secret = "test-secret"

            response = await test_client.post(
                "/api/auth/login",
                json={"email": "other@test.com", "password": "testpassword123"},
            )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_missing_fields(self, test_client):
        """Missing email/password returns 422 validation error."""
        response = await test_client.post("/api/auth/login", json={"email": "admin@test.com"})
        assert response.status_code == 422


class TestTokenVerification:

    def test_verify_valid_token(self):
        """A token created by _create_token can be decoded by _verify_token."""
        from app.api.auth import _create_token, _verify_token
        with patch("app.api.auth.settings") as mock_settings:
            mock_settings.nextauth_secret = "test-secret-for-verify"
            token = _create_token("admin@test.com")
            subject = _verify_token(token)
        assert subject == "admin@test.com"

    def test_verify_invalid_token(self):
        """Garbage token returns None."""
        from app.api.auth import _verify_token
        with patch("app.api.auth.settings") as mock_settings:
            mock_settings.nextauth_secret = "test-secret"
            result = _verify_token("not.a.valid.token")
        assert result is None

    def test_verify_wrong_secret(self):
        """Token signed with different secret returns None."""
        from app.api.auth import _create_token, _verify_token
        with patch("app.api.auth.settings") as mock_settings:
            mock_settings.nextauth_secret = "secret-A"
            token = _create_token("admin@test.com")

        with patch("app.api.auth.settings") as mock_settings:
            mock_settings.nextauth_secret = "secret-B"
            result = _verify_token(token)
        assert result is None


class TestRequireAdminDependency:

    @pytest.mark.asyncio
    async def test_require_admin_valid_token(self):
        """require_admin returns the subject for a valid token."""
        from app.api.auth import _create_token, require_admin
        with patch("app.api.auth.settings") as mock_settings:
            mock_settings.nextauth_secret = "test-secret"
            token = _create_token("admin@voicecare.ai")
            creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
            result = await require_admin(credentials=creds)
        assert result == "admin@voicecare.ai"

    @pytest.mark.asyncio
    async def test_require_admin_missing_token(self):
        """require_admin raises 401 when no credentials provided."""
        from app.api.auth import require_admin
        with pytest.raises(HTTPException) as exc_info:
            await require_admin(credentials=None)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_require_admin_invalid_token(self):
        """require_admin raises 401 for an expired or bad token."""
        from app.api.auth import require_admin
        with patch("app.api.auth._verify_token", return_value=None):
            creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="bad.token")
            with pytest.raises(HTTPException) as exc_info:
                await require_admin(credentials=creds)
            assert exc_info.value.status_code == 401


class TestDefaultCredentialGuard:

    @pytest.mark.asyncio
    async def test_login_blocked_with_defaults_outside_development(self, test_client):
        """403 when default secrets are configured in a production-like env."""
        from app.core.config import DEFAULT_ADMIN_PASSWORD

        with patch("app.api.auth.settings") as mock_settings:
            mock_settings.environment = "staging"
            mock_settings.admin_email = "admin@test.com"
            mock_settings.admin_password = DEFAULT_ADMIN_PASSWORD
            mock_settings.nextauth_secret = "real-secret"

            response = await test_client.post(
                "/api/auth/login",
                json={"email": "admin@test.com", "password": DEFAULT_ADMIN_PASSWORD},
            )

        assert response.status_code == 403
        assert "default credentials" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_allowed_with_defaults_in_development(self, test_client):
        """Local dev keeps working with the shipped defaults."""
        from app.core.config import DEFAULT_ADMIN_PASSWORD, DEFAULT_JWT_SECRET

        with patch("app.api.auth.settings") as mock_settings:
            mock_settings.environment = "development"
            mock_settings.admin_email = "admin@voicecare.ai"
            mock_settings.admin_password = DEFAULT_ADMIN_PASSWORD
            mock_settings.nextauth_secret = DEFAULT_JWT_SECRET

            response = await test_client.post(
                "/api/auth/login",
                json={"email": "admin@voicecare.ai", "password": DEFAULT_ADMIN_PASSWORD},
            )

        assert response.status_code == 200
        assert "access_token" in response.json()

    @pytest.mark.asyncio
    async def test_default_jwt_secret_alone_blocks_login(self, test_client):
        """A changed password but default JWT secret still blocks (forgeable tokens)."""
        from app.core.config import DEFAULT_JWT_SECRET

        with patch("app.api.auth.settings") as mock_settings:
            mock_settings.environment = "production"
            mock_settings.admin_email = "admin@test.com"
            mock_settings.admin_password = "a-strong-password"
            mock_settings.nextauth_secret = DEFAULT_JWT_SECRET

            response = await test_client.post(
                "/api/auth/login",
                json={"email": "admin@test.com", "password": "a-strong-password"},
            )

        assert response.status_code == 403


class TestLoginRateLimit:

    @pytest.mark.asyncio
    async def test_login_rate_limited_after_repeated_attempts(self, test_client):
        """The attempt after the per-IP limit returns 429 with Retry-After."""
        from app.core.config import get_settings

        limit = get_settings().login_rate_limit_per_15min
        with patch("app.api.auth.settings") as mock_settings:
            mock_settings.environment = "development"
            mock_settings.admin_email = "admin@test.com"
            mock_settings.admin_password = "correcthorse"
            mock_settings.nextauth_secret = "test-secret"

            for _ in range(limit):
                response = await test_client.post(
                    "/api/auth/login",
                    json={"email": "admin@test.com", "password": "wrong"},
                )
                assert response.status_code == 401

            response = await test_client.post(
                "/api/auth/login",
                json={"email": "admin@test.com", "password": "wrong"},
            )

        assert response.status_code == 429
        assert "Retry-After" in response.headers


class TestTokenExpiry:

    def test_token_expires_in_eight_hours(self):
        """Access tokens carry an 8-hour expiry claim."""
        from jose import jwt as jose_jwt

        from app.api.auth import _TOKEN_EXPIRE_HOURS, _create_token

        assert _TOKEN_EXPIRE_HOURS == 8

        with patch("app.api.auth.settings") as mock_settings:
            mock_settings.nextauth_secret = "expiry-secret"
            token = _create_token("admin@test.com")
            claims = jose_jwt.decode(token, "expiry-secret", algorithms=["HS256"])

        assert claims["exp"] - claims["iat"] == 8 * 3600


class TestLogoutRevocation:

    @pytest.mark.asyncio
    async def test_logout_revokes_token(self, test_client):
        """A token stops working the moment it is logged out."""
        from app.api.auth import _create_token

        with patch("app.api.auth.settings") as mock_settings:
            mock_settings.nextauth_secret = "revoke-secret"
            token = _create_token("admin@voicecare.ai")
            headers = {"Authorization": f"Bearer {token}"}

            before = await test_client.get("/api/auth/me", headers=headers)
            assert before.status_code == 200

            logout = await test_client.post("/api/auth/logout", headers=headers)
            assert logout.status_code == 200

            after = await test_client.get("/api/auth/me", headers=headers)
            assert after.status_code == 401

    @pytest.mark.asyncio
    async def test_logout_is_idempotent(self, test_client):
        """Logging out twice with the same token succeeds both times."""
        from app.api.auth import _create_token

        with patch("app.api.auth.settings") as mock_settings:
            mock_settings.nextauth_secret = "revoke-secret"
            token = _create_token("admin@voicecare.ai")
            headers = {"Authorization": f"Bearer {token}"}

            first = await test_client.post("/api/auth/logout", headers=headers)
            second = await test_client.post("/api/auth/logout", headers=headers)

        assert first.status_code == 200
        assert second.status_code == 200

    @pytest.mark.asyncio
    async def test_logout_does_not_revoke_other_tokens(self, test_client):
        """Revocation targets one jti — a fresh login still works."""
        from app.api.auth import _create_token

        with patch("app.api.auth.settings") as mock_settings:
            mock_settings.nextauth_secret = "revoke-secret"
            old_token = _create_token("admin@voicecare.ai")
            new_token = _create_token("admin@voicecare.ai")

            logout = await test_client.post(
                "/api/auth/logout", headers={"Authorization": f"Bearer {old_token}"}
            )
            assert logout.status_code == 200

            still_valid = await test_client.get(
                "/api/auth/me", headers={"Authorization": f"Bearer {new_token}"}
            )
        assert still_valid.status_code == 200

    @pytest.mark.asyncio
    async def test_logout_without_token_401(self, test_client):
        resp = await test_client.post("/api/auth/logout")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_logout_with_garbage_token_401(self, test_client):
        resp = await test_client.post(
            "/api/auth/logout", headers={"Authorization": "Bearer not.a.token"}
        )
        assert resp.status_code == 401

    def test_tokens_carry_unique_jti(self):
        """Every issued token gets its own jti claim."""
        from jose import jwt as jose_jwt

        from app.api.auth import _create_token

        with patch("app.api.auth.settings") as mock_settings:
            mock_settings.nextauth_secret = "jti-secret"
            a = jose_jwt.decode(_create_token("x"), "jti-secret", algorithms=["HS256"])
            b = jose_jwt.decode(_create_token("x"), "jti-secret", algorithms=["HS256"])

        assert a["jti"] and b["jti"]
        assert a["jti"] != b["jti"]


class TestWhoamiEndpoint:

    @pytest.mark.asyncio
    async def test_whoami_with_valid_token(self, test_client):
        """GET /api/auth/me returns admin email when authenticated."""
        from app.api.auth import _create_token

        # Keep the settings patch active through the request so the app decodes
        # with the same secret the token was signed with.
        with patch("app.api.auth.settings") as mock_settings:
            mock_settings.nextauth_secret = "test-secret"
            token = _create_token("admin@voicecare.ai")
            response = await test_client.get(
                "/api/auth/me",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 200
        assert response.json()["admin_email"] == "admin@voicecare.ai"

    @pytest.mark.asyncio
    async def test_whoami_without_token(self, test_client):
        """GET /api/auth/me returns 401 without Authorization header."""
        response = await test_client.get("/api/auth/me")
        assert response.status_code == 401

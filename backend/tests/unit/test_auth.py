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


class TestWhoamiEndpoint:

    @pytest.mark.asyncio
    async def test_whoami_with_valid_token(self, test_client):
        """GET /api/auth/me returns admin email when authenticated."""
        from app.api.auth import _create_token
        with patch("app.api.auth.settings") as mock_settings:
            mock_settings.nextauth_secret = "test-secret"
            token = _create_token("admin@voicecare.ai")

        with patch("app.api.auth._verify_token", return_value="admin@voicecare.ai"):
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

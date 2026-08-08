"""Тесты для core/auth_manager.py — аутентификация и токены"""

import asyncio
import base64
import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import jwt
import pytest
from fastapi import HTTPException

from core import auth_manager
from core.auth_manager import (
    AuthManager,
    get_auth_manager,
    get_user_id_from_token,
)

# Реальная функция, сохранённая до подмены conftest.test_app
_REAL_GET_CURRENT_USER_SAFE = auth_manager.get_current_user_safe


def _fake_jwt(payload: dict) -> str:
    """Генерирует структурно валидный JWT (для get_user_id_from_token)"""
    header = base64.urlsafe_b64encode(b'{"alg":"HS256","typ":"JWT"}').rstrip(b"=").decode()
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
    sig = "fakesignature"
    return f"{header}.{body}.{sig}"


def _signed_jwt(payload: dict) -> str:
    """Генерирует полноценный подписанный JWT (для jwt.decode)"""
    return jwt.encode(payload, "test-secret", algorithm="HS256")


@pytest.fixture
def auth_mgr():
    return AuthManager()


class TestValidateTokenFormat:
    def test_empty_token(self):
        mgr = AuthManager()
        ok, msg = mgr.validate_token_format("")
        assert not ok
        assert msg == "Токен не предоставлен"

    def test_valid_jwt(self):
        mgr = AuthManager()
        ok, msg = mgr.validate_token_format("abc.def.GHI")
        assert ok is True
        assert msg == ""

    def test_missing_parts(self):
        mgr = AuthManager()
        ok, msg = mgr.validate_token_format("abc.def")
        assert ok is False
        assert "Неверный формат" in msg

    def test_invalid_characters(self):
        mgr = AuthManager()
        ok, msg = mgr.validate_token_format("abc.def.ghi jkl")
        assert ok is False
        assert "недопустимые символы" in msg


class TestExtractTokenFromHeader:
    def test_no_header(self):
        mgr = AuthManager()
        assert mgr.extract_token_from_header(None) == (None, None)
        assert mgr.extract_token_from_header("") == (None, None)

    def test_missing_bearer_prefix(self):
        mgr = AuthManager()
        assert mgr.extract_token_from_header("Basic abc123") == (None, None)

    def test_access_only(self):
        mgr = AuthManager()
        access, refresh = mgr.extract_token_from_header("Bearer eyJaccess")
        assert access == "eyJaccess"
        assert refresh is None

    def test_access_and_refresh(self):
        mgr = AuthManager()
        access, refresh = mgr.extract_token_from_header("Bearer eyJaccess eyJrefresh")
        assert access == "eyJaccess"
        assert refresh == "eyJrefresh"


class TestValidateAndRefresh:
    """Классы ошибок с именами, похожими на supabase-py (AuthError/NetworkError)."""
    class _AuthError(Exception):
        pass

    class _NetworkError(Exception):
        pass

    def test_no_supabase(self):
        mgr = AuthManager()
        user, new_token, err = asyncio.run(mgr.validate_and_refresh(None, "abc.def.GHI"))
        assert user is None and new_token is None
        assert err == "БД не подключена"

    def test_invalid_token_format(self):
        mgr = AuthManager()
        supabase = MagicMock()
        user, new_token, err = asyncio.run(mgr.validate_and_refresh(supabase, "not-a-jwt"))
        assert user is None
        assert "Неверный формат" in err

    def test_valid_token_returns_user(self):
        """Валидный токен (get_user успешен) возвращает пользователя"""
        mgr = AuthManager()
        supabase = MagicMock()
        supabase.auth.get_user.return_value.user = SimpleNamespace(
            id="user-123", email="a@b.c"
        )

        token = _fake_jwt({"sub": "user-123", "email": "a@b.c"})
        user, new_token, err = asyncio.run(
            mgr.validate_and_refresh(supabase, token)
        )
        assert user == {"user": supabase.auth.get_user.return_value.user}
        assert new_token is None
        assert err == ""

    def test_expired_token_refresh_fails(self):
        """Токен просрочен, refresh неудачен — возвращает ошибку"""
        mgr = AuthManager()
        supabase = MagicMock()
        supabase.auth.get_user.side_effect = Exception("token has expired")
        supabase.auth.refresh_session.side_effect = Exception("bad refresh token")

        token = _fake_jwt({"sub": "user-123"})
        user, new_token, err = asyncio.run(
            mgr.validate_and_refresh(supabase, token, refresh_token="bad-refresh")
        )
        assert user is None
        assert "Неверный refresh токен" in err

    def test_expired_token_no_refresh(self):
        """Токен просрочен, refresh не передан — generic ошибка"""
        mgr = AuthManager()
        supabase = MagicMock()
        supabase.auth.get_user.side_effect = Exception("token expired")

        user, new_token, err = asyncio.run(
            mgr.validate_and_refresh(supabase, "a.b.c")
        )
        assert user is None
        assert new_token is None
        assert "истек или невалиден" in err

    def test_refresh_success_returns_new_token(self):
        """Refresh успешен — возвращает нового пользователя и новый access token"""
        mgr = AuthManager()
        supabase = MagicMock()
        supabase.auth.get_user.side_effect = [
            Exception("token expired"),
            SimpleNamespace(user=SimpleNamespace(id="user-123", email="a@b.c")),
        ]
        session = SimpleNamespace(access_token="new-access-token")
        supabase.auth.refresh_session.return_value = SimpleNamespace(session=session)

        token = _fake_jwt({"sub": "user-123"})
        user, new_token, err = asyncio.run(
            mgr.validate_and_refresh(supabase, token, refresh_token="good-refresh")
        )
        assert user["user"].id == "user-123"
        assert user["user"].email == "a@b.c"
        assert new_token == "new-access-token"
        assert err == ""

    def test_auth_error_classification(self):
        """AuthError → «Неверные учетные данные» (ранее недостижимая ветка)"""
        mgr = AuthManager()
        supabase = MagicMock()
        supabase.auth.get_user.side_effect = self._AuthError("invalid credentials")

        user, new_token, err = asyncio.run(
            mgr.validate_and_refresh(supabase, "a.b.c")
        )
        assert user is None
        assert err == "Неверные учетные данные"

    def test_network_error_classification(self):
        """NetworkError → возвращаемся сразу, без попытки refresh"""
        mgr = AuthManager()
        supabase = MagicMock()
        supabase.auth.get_user.side_effect = self._NetworkError("connection refused")

        user, new_token, err = asyncio.run(
            mgr.validate_and_refresh(supabase, "a.b.c", refresh_token="some-refresh")
        )
        assert user is None
        assert err == "Ошибка подключения к серверу аутентификации"
        supabase.auth.refresh_session.assert_not_called()

    def test_generic_error_falls_back(self):
        """Произвольная ошибка (не Auth/Network) — generic «истек или невалиден»"""
        mgr = AuthManager()
        supabase = MagicMock()
        supabase.auth.get_user.side_effect = RuntimeError("strange failure")

        user, new_token, err = asyncio.run(
            mgr.validate_and_refresh(supabase, "a.b.c")
        )
        assert user is None
        assert "истек или невалиден" in err


class TestGetCurrentUserSafe:
    def test_no_authorization_header(self):
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(_REAL_GET_CURRENT_USER_SAFE(None))
        assert exc_info.value.status_code == 401

    def test_missing_bearer(self):
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(_REAL_GET_CURRENT_USER_SAFE("Basic foo"))
        assert exc_info.value.status_code == 401

    def test_dev_mode_no_supabase(self, monkeypatch):
        """В DEV-режиме без БД — локальный токен"""
        import core.supabase_client

        monkeypatch.setattr(core.supabase_client, "_is_development", lambda: True)
        monkeypatch.setattr(core.supabase_client, "get_supabase", lambda: None)

        token = _signed_jwt({"sub": "dev-user-1", "email": "dev@local"})
        result = asyncio.run(_REAL_GET_CURRENT_USER_SAFE(f"Bearer {token}"))
        assert result["id"] == "dev-user-1"
        assert result["email"] == "dev@local"

    def test_expired_token_raises_401(self, monkeypatch):
        """Просроченный токен — HTTPException 401 с requires_login"""
        import core.supabase_client

        mock_supabase = MagicMock()
        mock_supabase.auth.get_user.side_effect = Exception("token has expired")
        monkeypatch.setattr(core.supabase_client, "get_supabase", lambda: mock_supabase)
        monkeypatch.setattr(core.supabase_client, "_is_development", lambda: False)

        token = _signed_jwt({"sub": "user-1"})
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(_REAL_GET_CURRENT_USER_SAFE(f"Bearer {token}"))
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["requires_login"] is True


class TestGetUserIdFromToken:
    def test_valid_token(self):
        token = _fake_jwt({"sub": "user-abc", "email": "x@y.z"})
        assert get_user_id_from_token(token) == "user-abc"

    def test_malformed_token(self):
        assert get_user_id_from_token("not a jwt") is None
        assert get_user_id_from_token(None) is None

    def test_no_sub(self):
        token = _fake_jwt({"email": "x@y.z"})
        assert get_user_id_from_token(token) is None


class TestSingleton:
    def test_singleton_instance(self):
        assert get_auth_manager() is get_auth_manager()


class TestAuthRequired:
    def test_decorator_without_request_no_auth(self):
        """Без request в аргументах декоратор не авторизует (передаёт управление дальше)"""
        @auth_manager.auth_required
        async def handler(*args, **kwargs):
            return {"ok": True}

        result = asyncio.run(handler())
        assert result == {"ok": True}

    def test_decorator_with_request_requires_authorization(self):
        """С request без Authorization — HTTPException 401"""
        from fastapi import Request

        request = MagicMock(spec=Request)
        request.headers = {"Authorization": None}

        @auth_manager.auth_required
        async def handler(*args, **kwargs):
            return {"ok": True}

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(handler(request))
        assert exc_info.value.status_code == 401


class TestGetCurrentUserAlias:
    def test_alias_delegates_to_safe(self, monkeypatch):
        """get_current_user — обёртка над get_current_user_safe (для совместимости)"""
        called = {}

        async def fake_safe(authorization=None, x_refresh_token=None):
            called["authorization"] = authorization
            called["x_refresh_token"] = x_refresh_token
            return {"ok": True}

        monkeypatch.setattr(auth_manager, "get_current_user_safe", fake_safe)
        result = asyncio.run(auth_manager.get_current_user("Bearer x", "refresh-y"))
        assert result == {"ok": True}
        assert called == {"authorization": "Bearer x", "x_refresh_token": "refresh-y"}

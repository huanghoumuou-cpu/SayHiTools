from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException, Request, Response, status


SESSION_COOKIE_NAME = "sayhi_session"
SESSION_TTL_SECONDS = 7 * 24 * 60 * 60


@dataclass(frozen=True)
class AuthConfig:
    username: str
    password: str
    secret: str
    cookie_secure: bool

    @property
    def is_configured(self) -> bool:
        return bool(self.username and self.password and self.secret)


@dataclass(frozen=True)
class SessionData:
    username: str
    expires_at: int
    session_id: str


def get_auth_config() -> AuthConfig:
    return AuthConfig(
        username=os.getenv("SAYHI_ADMIN_USERNAME", "").strip(),
        password=os.getenv("SAYHI_ADMIN_PASSWORD", ""),
        secret=os.getenv("SAYHI_SESSION_SECRET", ""),
        cookie_secure=os.getenv("SAYHI_COOKIE_SECURE", "false").strip().lower() in {"1", "true", "yes", "on"},
    )


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _sign(payload: str, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), payload.encode("ascii"), hashlib.sha256).digest()
    return _b64encode(digest)


def create_session_token(config: AuthConfig) -> str:
    expires_at = int(time.time()) + SESSION_TTL_SECONDS
    payload = {
        "u": config.username,
        "exp": expires_at,
        "sid": secrets.token_urlsafe(18),
    }
    encoded_payload = _b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = _sign(encoded_payload, config.secret)
    return f"{encoded_payload}.{signature}"


def parse_session_token(token: str, config: AuthConfig) -> SessionData | None:
    if not config.is_configured or "." not in token:
        return None
    encoded_payload, signature = token.split(".", 1)
    expected_signature = _sign(encoded_payload, config.secret)
    if not hmac.compare_digest(signature, expected_signature):
        return None
    try:
        payload: dict[str, Any] = json.loads(_b64decode(encoded_payload))
    except (ValueError, json.JSONDecodeError):
        return None

    username = str(payload.get("u") or "")
    expires_at = int(payload.get("exp") or 0)
    session_id = str(payload.get("sid") or "")
    if username != config.username or not session_id or expires_at <= int(time.time()):
        return None
    return SessionData(username=username, expires_at=expires_at, session_id=session_id)


def get_session_from_request(request: Request) -> SessionData | None:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        return None
    return parse_session_token(token, get_auth_config())


def require_auth(request: Request) -> SessionData:
    session = get_session_from_request(request)
    if session is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="请先登录")
    return session


def verify_admin_credentials(username: str, password: str) -> AuthConfig:
    config = get_auth_config()
    if not config.is_configured:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="管理员登录未配置")
    username_ok = hmac.compare_digest(username, config.username)
    password_ok = hmac.compare_digest(password, config.password)
    if not (username_ok and password_ok):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    return config


def set_session_cookie(response: Response, config: AuthConfig) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=create_session_token(config),
        max_age=SESSION_TTL_SECONDS,
        httponly=True,
        secure=config.cookie_secure,
        samesite="lax",
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/", samesite="lax")

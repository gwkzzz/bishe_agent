from __future__ import annotations

from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings


ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_access_token(subject: str, username: str) -> str:
    settings = get_settings()
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": subject,
        "username": username,
        "exp": expires_at,
    }
    return jwt.encode(payload, settings.server_secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, str]:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.server_secret_key, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise ValueError("Invalid access token") from exc
    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject:
        raise ValueError("Invalid access token subject")
    return payload

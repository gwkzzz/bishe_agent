from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.integrations.errors import ObjectStorageError
from app.integrations.minio_client import MinIOClient
from app.models import User
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    ProfileUpdateRequest,
    RegisterRequest,
    RegisterResponse,
    UserRead,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])
MAX_AVATAR_BYTES = 2 * 1024 * 1024
ALLOWED_AVATAR_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest,
    db: Annotated[Session, Depends(get_db)],
) -> RegisterResponse:
    username = payload.username.strip()
    if not username:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Username required.")

    existing = db.scalar(select(User).where(User.username == username))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already registered.",
        )

    user = User(username=username, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return RegisterResponse(user=user)


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Annotated[Session, Depends(get_db)]) -> LoginResponse:
    username = payload.username.strip()
    if not username:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Username required.")

    user = db.scalar(select(User).where(User.username == username))

    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )

    return LoginResponse(
        access_token=create_access_token(subject=user.id, username=user.username),
        user=user,
    )


@router.get("/me", response_model=UserRead)
def read_me(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    return current_user


@router.patch("/me", response_model=UserRead)
def update_me(
    payload: ProfileUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    current_user.signature = payload.signature.strip() if payload.signature else None
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/me/avatar", response_model=UserRead)
def upload_avatar(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    file: Annotated[UploadFile, File()],
) -> User:
    if file.content_type not in ALLOWED_AVATAR_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Avatar must be a JPEG, PNG, WebP, or GIF image.",
        )

    file.file.seek(0, 2)
    length = file.file.tell()
    file.file.seek(0)
    if length <= 0 or length > MAX_AVATAR_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Avatar image must be smaller than 2MB.",
        )

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        suffix = _suffix_from_content_type(file.content_type)
    object_name = f"users/{current_user.id}/avatar{suffix}"

    try:
        MinIOClient().put_object(
            object_name=object_name,
            data=file.file,
            length=length,
            content_type=file.content_type or "application/octet-stream",
        )
    except ObjectStorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Avatar upload failed.",
        ) from exc

    current_user.avatar_object_key = object_name
    current_user.avatar_content_type = file.content_type
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/users/{user_id}/avatar")
def get_user_avatar(user_id: str, db: Annotated[Session, Depends(get_db)]) -> Response:
    user = db.get(User, user_id)
    return _avatar_response(user)


@router.get("/users/by-name/{username}/avatar")
def get_user_avatar_by_name(username: str, db: Annotated[Session, Depends(get_db)]) -> Response:
    user = db.scalar(select(User).where(User.username == username))
    return _avatar_response(user)


def _avatar_response(user: User | None) -> Response:
    if user is None or not user.avatar_object_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Avatar not found.")

    try:
        content = MinIOClient().get_object_bytes(user.avatar_object_key)
    except ObjectStorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Avatar not found.",
        ) from exc

    return Response(
        content=content,
        media_type=user.avatar_content_type or "application/octet-stream",
        headers={"Cache-Control": "private, max-age=60"},
    )


def _suffix_from_content_type(content_type: str | None) -> str:
    mapping = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/gif": ".gif",
    }
    return mapping.get(content_type or "", ".png")

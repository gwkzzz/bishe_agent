from __future__ import annotations

from urllib.parse import quote

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin


class User(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_object_key: Mapped[str | None] = mapped_column(String(512))
    avatar_content_type: Mapped[str | None] = mapped_column(String(128))
    signature: Mapped[str | None] = mapped_column(String(255))

    cases: Mapped[list["LegalCase"]] = relationship(back_populates="user")
    chat_messages: Mapped[list["ChatMessage"]] = relationship(back_populates="user")

    @property
    def avatar_url(self) -> str | None:
        if not self.avatar_object_key:
            return None
        return f"/api/auth/users/by-name/{quote(self.username, safe='')}/avatar"


from app.models.case import ChatMessage, LegalCase  # noqa: E402

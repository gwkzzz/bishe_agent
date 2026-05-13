from typing import Annotated

from fastapi import Header, HTTPException, status

from app.core.config import get_settings


async def verify_internal_token(
    x_internal_token: Annotated[str | None, Header(alias="X-Internal-Token")] = None,
) -> None:
    settings = get_settings()
    if x_internal_token != settings.algorithm_internal_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal token.",
        )

from fastapi import APIRouter, Request

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(request: Request) -> dict[str, str | None]:
    return {
        "status": "ok",
        "service": "server",
        "trace_id": getattr(request.state, "trace_id", None),
    }

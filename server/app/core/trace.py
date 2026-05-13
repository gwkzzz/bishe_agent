from uuid import uuid4

from fastapi import Request, Response

from app.core.config import get_settings


async def trace_middleware(request: Request, call_next) -> Response:
    settings = get_settings()
    trace_id = request.headers.get(settings.trace_header_name) or str(uuid4())
    request.state.trace_id = trace_id
    response = await call_next(request)
    response.headers[settings.trace_header_name] = trace_id
    return response

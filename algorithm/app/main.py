from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.trace import trace_middleware


settings = get_settings()
configure_logging(settings.log_level)

app = FastAPI(
    title="Legal Assistant Algorithm",
    version="0.1.0",
    description="Algorithm and agent service for the legal multi-agent assistant.",
)

app.middleware("http")(trace_middleware)
app.include_router(api_router)

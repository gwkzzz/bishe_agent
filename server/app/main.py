from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.trace import trace_middleware


settings = get_settings()
configure_logging(settings.log_level)

app = FastAPI(
    title="Legal Assistant Server",
    version="0.1.0",
    description="Business API service for the legal multi-agent assistant.",
)

app.middleware("http")(trace_middleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

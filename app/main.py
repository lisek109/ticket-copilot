from fastapi import FastAPI

from app.api.routes import router as api_router
from app.auth.routes import router as auth_router
from app.core.logging_config import configure_logging

configure_logging()

app = FastAPI(title="Ticket/Email Copilot", version="0.1.0")

app.include_router(api_router)
app.include_router(auth_router)
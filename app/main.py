from fastapi import FastAPI
from app.api.routes import router

# Main FastAPI application entrypoint
app = FastAPI(title="Ticket/Email Copilot", version="0.1.0")

# Register API routes
app.include_router(router)

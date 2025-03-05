from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.api.routes import router as api_router
from app.core.config import settings
from app.utils.logger import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup before startup
    setup_logging()
    logging.info("Starting Multi-Agent Orchestration Platform")
    yield
    # Cleanup on shutdown
    logging.info("Shutting down Multi-Agent Orchestration Platform")


app = FastAPI(
    title="Multi-Agent Orchestration Platform",
    description="A platform for orchestrating LangGraph-based agent applications",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")

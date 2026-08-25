from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
from app.routers import (
    health, documents, chat, comparison, research, reports, workflows, analytics, workspaces, background_tasks
)
from app.workflows.runner import runner


@asynccontextmanager
async def lifespan(app: FastAPI):
    await runner.start()
    yield
    await runner.shutdown()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Enterprise AI Workspace: Understands, analyzes, compares, and acts on your documents",
    version="2.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

cors_origins = settings.cors_origins_list or (["*"] if settings.ENVIRONMENT == "development" else [])
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix=settings.API_V1_STR)
app.include_router(documents.router, prefix=settings.API_V1_STR)
app.include_router(chat.router, prefix=settings.API_V1_STR)
app.include_router(comparison.router, prefix=settings.API_V1_STR)
app.include_router(research.router, prefix=settings.API_V1_STR)
app.include_router(reports.router, prefix=settings.API_V1_STR)
app.include_router(workflows.router, prefix=settings.API_V1_STR)
app.include_router(analytics.router, prefix=settings.API_V1_STR)
app.include_router(background_tasks.router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    return {
        "message": "Welcome to Knowly 2.0 Document AI Workspace API",
        "docs": "/docs",
        "version": "2.0.0",
        "environment": settings.ENVIRONMENT,
    }

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import router
from app.config import settings
from app.core.exceptions import AppException
from app.core.logging import setup_logging
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging("DEBUG" if settings.DEBUG else "INFO")
    if settings.ENVIRONMENT == "development":
        await init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="BBA Services Entrepreneur Command OS Powered by The Noble Savage",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred"},
    )


app.include_router(router)


@app.get("/health")
async def health_check() -> dict:
    return {"status": "ok", "service": settings.APP_NAME, "environment": settings.ENVIRONMENT}

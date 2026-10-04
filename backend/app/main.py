"""The FastAPI application."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient

from app.api import analytics, employees
from app.config import settings
from app.persistence.database import connect


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    client: AsyncIOMotorClient[dict[str, Any]] = AsyncIOMotorClient(settings.mongodb_url)
    await connect(client, settings.database_name)
    yield
    client.close()


app = FastAPI(title="ACME Salary Management", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(employees.router)
app.include_router(analytics.router)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}

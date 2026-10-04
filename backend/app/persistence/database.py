"""Connecting Beanie to MongoDB."""

from __future__ import annotations

from typing import Any

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from app.persistence.models import Band, Employee, Rate


async def connect(client: AsyncIOMotorClient[dict[str, Any]], database: str) -> None:
    await init_beanie(database=client[database], document_models=[Employee, Band, Rate])

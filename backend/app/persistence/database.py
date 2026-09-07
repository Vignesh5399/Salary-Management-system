"""Connecting Beanie to MongoDB."""

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from app.persistence.models import Employee


async def connect(client: AsyncIOMotorClient, database: str) -> None:
    await init_beanie(database=client[database], document_models=[Employee])

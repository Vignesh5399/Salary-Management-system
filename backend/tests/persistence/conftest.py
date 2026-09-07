import os
from collections.abc import AsyncIterator

import pytest

MONGODB_URL = os.environ.get("MONGODB_URL")


@pytest.fixture
async def repository() -> AsyncIterator[object]:
    """A repository over a throwaway database, dropped after each test."""
    if not MONGODB_URL:
        pytest.skip("set MONGODB_URL to run integration tests")

    from motor.motor_asyncio import AsyncIOMotorClient

    from app.persistence.database import connect
    from app.persistence.repository import EmployeeRepository

    client = AsyncIOMotorClient(MONGODB_URL)
    database_name = "salary_test"
    await connect(client, database_name)
    try:
        yield EmployeeRepository()
    finally:
        await client.drop_database(database_name)
        client.close()

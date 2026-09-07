"""The stored shape of an employee.

Compensation is embedded rather than held in its own collection. A pay history
is only ever read or written whole, and embedding makes closing one record and
opening its successor a single atomic document update.
"""

from datetime import datetime

import pymongo
from beanie import Document
from pydantic import BaseModel, Field


class CompensationEntry(BaseModel):
    """One salary and the window it applied to. Written only via the repository."""

    amount_minor: int
    currency: str
    effective_from: datetime
    effective_to: datetime | None = None
    reason: str


class Employee(Document):
    employee_no: str
    name: str
    email: str
    country: str
    department: str
    level: str
    job_title: str
    hire_date: datetime
    status: str = "active"
    compensation: list[CompensationEntry] = Field(default_factory=list)

    class Settings:
        name = "employees"
        indexes = [
            pymongo.IndexModel([("employee_no", pymongo.ASCENDING)], unique=True),
            pymongo.IndexModel([("country", pymongo.ASCENDING)]),
            pymongo.IndexModel([("department", pymongo.ASCENDING)]),
            pymongo.IndexModel(
                [("country", pymongo.ASCENDING), ("level", pymongo.ASCENDING)]
            ),
        ]

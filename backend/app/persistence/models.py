"""The stored shape of an employee.

Compensation is embedded rather than held in its own collection. A pay history
is only ever read or written whole, and embedding makes closing one record and
opening its successor a single atomic document update.
"""

from datetime import datetime
from typing import ClassVar

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

    # Denormalised from the last compensation entry. Duplication, deliberately:
    # it makes sorting and below-band queries ordinary indexed reads instead of
    # array arithmetic. Kept correct by writing compensation through one path.
    current_amount_minor: int = 0
    current_currency: str = ""

    class Settings:
        name = "employees"
        indexes: ClassVar[list[pymongo.IndexModel]] = [
            pymongo.IndexModel([("employee_no", pymongo.ASCENDING)], unique=True),
            pymongo.IndexModel([("country", pymongo.ASCENDING)]),
            pymongo.IndexModel([("department", pymongo.ASCENDING)]),
            pymongo.IndexModel([("country", pymongo.ASCENDING), ("level", pymongo.ASCENDING)]),
            pymongo.IndexModel([("current_amount_minor", pymongo.DESCENDING)]),
            pymongo.IndexModel([("name", pymongo.ASCENDING)]),
        ]


class Band(Document):
    """A pay range for one level in one country."""

    level: str
    country: str
    currency: str
    minimum_minor: int
    midpoint_minor: int
    maximum_minor: int

    class Settings:
        name = "bands"
        indexes: ClassVar[list[pymongo.IndexModel]] = [
            pymongo.IndexModel(
                [("level", pymongo.ASCENDING), ("country", pymongo.ASCENDING)],
                unique=True,
            )
        ]


class Rate(Document):
    """One unit of `base` in `quote`, from `effective_from`."""

    base: str
    quote: str
    rate: str  # Decimal as a string; BSON Decimal128 buys nothing here
    effective_from: datetime

    class Settings:
        name = "rates"
        indexes: ClassVar[list[pymongo.IndexModel]] = [
            pymongo.IndexModel([("base", pymongo.ASCENDING), ("quote", pymongo.ASCENDING)])
        ]

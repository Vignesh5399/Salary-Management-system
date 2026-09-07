"""Reading and writing employees. The only place compensation is persisted."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from app.domain.compensation import ChangeReason, CompensationHistory
from app.domain.money import Money
from app.persistence.documents import (
    compensation_from_documents,
    compensation_to_documents,
)
from app.persistence.guards import EmptyHistory, raise_guard
from app.persistence.models import CompensationEntry, Employee


class ConcurrentChange(RuntimeError):
    """Raised when the stored history moved between reading it and writing it back."""


class UnknownEmployee(LookupError):
    """Raised when no employee has the given number."""


class EmployeeRepository:
    async def add(self, employee: Mapping[str, Any]) -> Employee:
        """Create an employee with their hire salary as the first record."""
        details = dict(employee)
        starting_salary: Money = details.pop("starting_salary")
        hire_date: date = details.pop("hire_date")

        history = CompensationHistory.starting_with(starting_salary, on=hire_date)
        document = Employee(
            **details,
            hire_date=datetime(hire_date.year, hire_date.month, hire_date.day),
            compensation=_entries(history),
            **_current_fields(history),
        )
        return await document.insert()

    async def get(self, employee_no: str) -> Employee | None:
        return await Employee.find_one(Employee.employee_no == employee_no)

    async def compensation_of(self, employee_no: str) -> CompensationHistory:
        employee = await self._require(employee_no)
        return _history(employee)

    async def list(
        self,
        *,
        page: int = 1,
        size: int = 50,
        country: str | None = None,
        department: str | None = None,
    ) -> tuple[list[Employee], int]:
        criteria: dict[str, Any] = {}
        if country:
            criteria["country"] = country
        if department:
            criteria["department"] = department

        query = Employee.find(criteria)
        total = await query.count()
        employees = await query.sort("name").skip((page - 1) * size).limit(size).to_list()
        return employees, total

    async def count_below_band(self, bands: Sequence[Any]) -> int:
        """How many people sit under the bottom of their own band."""
        if not bands:
            return 0
        return await Employee.find(
            {
                "status": "active",
                "$or": [
                    {
                        "country": band.country,
                        "level": band.level,
                        "current_amount_minor": {"$lt": band.minimum_minor},
                    }
                    for band in bands
                ],
            }
        ).count()

    async def payroll_by(self, dimension: str) -> list[dict[str, Any]]:
        """Headcount and total pay per group, per currency. Converted by the caller."""
        return await Employee.get_motor_collection().aggregate(
            [
                {"$match": {"status": "active"}},
                {
                    "$group": {
                        "_id": {"group": f"${dimension}", "currency": "$current_currency"},
                        "headcount": {"$sum": 1},
                        "total_minor": {"$sum": "$current_amount_minor"},
                    }
                },
                {"$sort": {"_id.group": 1}},
            ]
        ).to_list(length=None)

    async def apply_raise(
        self,
        employee_no: str,
        *,
        percent: Decimal,
        effective_from: date,
        reason: ChangeReason,
    ) -> CompensationHistory:
        employee = await self._require(employee_no)
        current = _history(employee)
        raised = current.raise_by(percent, effective_from=effective_from, reason=reason)
        await self.replace_compensation(employee_no, raised, expecting=current)
        return raised

    async def replace_compensation(
        self,
        employee_no: str,
        replacement: CompensationHistory,
        *,
        expecting: CompensationHistory,
    ) -> None:
        """Write a new history, but only if the stored one still matches ``expecting``."""
        result = await Employee.get_motor_collection().update_one(
            raise_guard(employee_no, compensation_to_documents(expecting)),
            {
                "$set": {
                    "compensation": compensation_to_documents(replacement),
                    **_current_fields(replacement),
                }
            },
        )
        if result.matched_count == 0:
            raise ConcurrentChange(
                f"{employee_no}'s compensation changed since it was read"
            )

    async def _require(self, employee_no: str) -> Employee:
        employee = await self.get(employee_no)
        if employee is None:
            raise UnknownEmployee(employee_no)
        return employee


def _current_fields(history: CompensationHistory) -> dict[str, Any]:
    return {
        "current_amount_minor": history.current.amount_minor,
        "current_currency": history.current.currency.code,
    }


def _entries(history: CompensationHistory) -> list[CompensationEntry]:
    return [CompensationEntry(**document) for document in compensation_to_documents(history)]


def _history(employee: Employee) -> CompensationHistory:
    if not employee.compensation:
        raise EmptyHistory(f"{employee.employee_no} has no compensation records")
    return compensation_from_documents([entry.model_dump() for entry in employee.compensation])

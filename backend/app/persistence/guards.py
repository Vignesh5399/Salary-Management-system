"""Concurrency guards for compensation writes.

Kept free of any driver import so it can be tested without a database — this
is the subtle part of the persistence layer and it should be in the fast suite.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


class EmptyHistory(ValueError):
    """Raised when an employee has no compensation records at all."""


def raise_guard(employee_no: str, current: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """The filter that makes replacing a compensation history safe.

    MongoDB gives us atomicity within one document but no transaction across the
    read and the write. This pins the state we read from: the same employee, the
    same number of records, and a last record that is still open and still starts
    where we saw it start. If anything changed, the update matches nothing rather
    than overwriting someone else's work.
    """
    if not current:
        raise EmptyHistory(f"{employee_no} has no compensation history to supersede")

    last = len(current) - 1
    return {
        "employee_no": employee_no,
        "compensation": {"$size": len(current)},
        f"compensation.{last}.effective_to": None,
        f"compensation.{last}.effective_from": current[last]["effective_from"],
    }

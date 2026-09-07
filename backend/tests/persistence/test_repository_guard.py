from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from app.domain.compensation import ChangeReason, CompensationHistory
from app.domain.money import Money
from app.persistence.documents import compensation_to_documents
from app.persistence.repository import EmptyHistory, raise_guard

HIRED = date(2022, 4, 1)


def _documents(raises: int = 0) -> list[dict]:
    history = CompensationHistory.starting_with(Money.of("100000.00", "INR"), on=HIRED)
    for year in range(raises):
        history = history.raise_by(
            Decimal("10"),
            effective_from=date(2023 + year, 4, 1),
            reason=ChangeReason.MERIT,
        )
    return compensation_to_documents(history)


def test_the_guard_targets_one_employee() -> None:
    assert raise_guard("ACM-1", _documents())["employee_no"] == "ACM-1"


def test_the_guard_pins_the_number_of_records() -> None:
    # If another write appended a record since we read, the size no longer
    # matches and the update finds nothing rather than clobbering it.
    assert raise_guard("ACM-1", _documents(raises=2))["compensation"] == {"$size": 3}


def test_the_guard_requires_the_last_record_to_still_be_open() -> None:
    guard = raise_guard("ACM-1", _documents(raises=1))

    assert guard["compensation.1.effective_to"] is None


def test_the_guard_pins_the_start_date_of_the_record_it_supersedes() -> None:
    guard = raise_guard("ACM-1", _documents(raises=1))

    assert guard["compensation.1.effective_from"] == datetime(2023, 4, 1, tzinfo=UTC)


def test_the_guard_indexes_from_zero_for_a_new_hire() -> None:
    guard = raise_guard("ACM-1", _documents())

    assert guard["compensation.0.effective_to"] is None
    assert guard["compensation.0.effective_from"] == datetime(2022, 4, 1, tzinfo=UTC)


def test_a_guard_cannot_be_built_without_a_history() -> None:
    with pytest.raises(EmptyHistory):
        raise_guard("ACM-1", [])

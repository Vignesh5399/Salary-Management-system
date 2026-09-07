"""Repository tests against a real MongoDB.

Marked ``integration`` and excluded from the default run. Set MONGODB_URL to
any reachable MongoDB — an Atlas free cluster is enough:

    MONGODB_URL='mongodb+srv://...' pytest -m integration

The fixture uses a separate 'salary_test' database and drops it after each
test, so pointing this at the same cluster as the app is safe.
"""

from datetime import date
from decimal import Decimal

import pytest

from app.domain.compensation import ChangeReason
from app.domain.money import Money
from app.persistence.repository import ConcurrentChange, EmployeeRepository

pytestmark = pytest.mark.integration

HIRED = date(2022, 4, 1)
RAISED = date(2023, 4, 1)


async def test_an_employee_can_be_stored_and_read_back(repository: EmployeeRepository) -> None:
    await repository.add(_priya())

    found = await repository.get("ACM-1")

    assert found is not None
    assert found.name == "Priya R"


async def test_a_stored_employee_keeps_their_current_salary(
    repository: EmployeeRepository,
) -> None:
    await repository.add(_priya())

    history = await repository.compensation_of("ACM-1")

    assert history.current == Money.of("100000.00", "INR")


async def test_an_unknown_employee_is_not_found(repository: EmployeeRepository) -> None:
    assert await repository.get("nobody") is None


async def test_applying_a_raise_changes_the_current_salary(
    repository: EmployeeRepository,
) -> None:
    await repository.add(_priya())

    await repository.apply_raise(
        "ACM-1", percent=Decimal("10"), effective_from=RAISED, reason=ChangeReason.MERIT
    )

    history = await repository.compensation_of("ACM-1")
    assert history.current == Money.of("110000.00", "INR")


async def test_applying_a_raise_keeps_the_previous_salary_answerable(
    repository: EmployeeRepository,
) -> None:
    await repository.add(_priya())

    await repository.apply_raise(
        "ACM-1", percent=Decimal("10"), effective_from=RAISED, reason=ChangeReason.MERIT
    )

    history = await repository.compensation_of("ACM-1")
    assert history.salary_on(date(2023, 3, 31)) == Money.of("100000.00", "INR")


async def test_a_raise_is_rejected_if_the_history_moved_under_us(
    repository: EmployeeRepository,
) -> None:
    # Two raises computed from the same read. The second must fail rather than
    # overwrite the first — this is what stands in for a transaction.
    await repository.add(_priya())
    stale = await repository.compensation_of("ACM-1")

    await repository.apply_raise(
        "ACM-1", percent=Decimal("10"), effective_from=RAISED, reason=ChangeReason.MERIT
    )

    with pytest.raises(ConcurrentChange):
        await repository.replace_compensation(
            "ACM-1",
            stale.raise_by(
                Decimal("20"), effective_from=RAISED, reason=ChangeReason.PROMOTION
            ),
            expecting=stale,
        )


async def test_employees_can_be_listed_a_page_at_a_time(
    repository: EmployeeRepository,
) -> None:
    for number in range(1, 6):
        await repository.add(_priya(employee_no=f"ACM-{number}"))

    page, total = await repository.list(page=1, size=2)

    assert len(page) == 2
    assert total == 5


async def test_employees_can_be_filtered_by_country(repository: EmployeeRepository) -> None:
    await repository.add(_priya(employee_no="ACM-1", country="IN"))
    await repository.add(_priya(employee_no="ACM-2", country="GB"))

    _, total = await repository.list(page=1, size=10, country="GB")

    assert total == 1


def _priya(employee_no: str = "ACM-1", country: str = "IN") -> dict:
    return {
        "employee_no": employee_no,
        "name": "Priya R",
        "email": f"{employee_no.lower()}@acme.example",
        "country": country,
        "department": "Engineering",
        "level": "L4",
        "job_title": "Senior Engineer",
        "hire_date": HIRED,
        "starting_salary": Money.of("100000.00", "INR"),
    }

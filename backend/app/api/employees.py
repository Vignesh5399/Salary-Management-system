"""Employee endpoints."""

from fastapi import APIRouter, HTTPException, Query

from app.api.bands import load_bands, place
from app.api.schemas import (
    EmployeeDetailOut,
    EmployeeSummaryOut,
    PageOut,
    RaiseIn,
)
from app.domain.compensation import InvalidCompensationChange
from app.domain.currency import Currency
from app.domain.money import Money
from app.persistence.repository import (
    ConcurrentChange,
    EmployeeRepository,
    UnknownEmployee,
)

router = APIRouter(prefix="/api/employees", tags=["employees"])
repository = EmployeeRepository()


@router.get("", response_model=PageOut)
async def list_employees(
    page: int = Query(1, ge=1),
    size: int = Query(25, ge=1, le=100),
    country: str | None = None,
    department: str | None = None,
) -> PageOut:
    employees, total = await repository.list(
        page=page, size=size, country=country, department=department
    )
    bands = await load_bands()

    items = []
    for employee in employees:
        summary = EmployeeSummaryOut.of(employee)
        placement = place(
            bands,
            level=employee.level,
            country=employee.country,
            salary=Money(employee.current_amount_minor, Currency.of(employee.current_currency)),
        )
        if placement:
            position, ratio = placement
            summary.band_position = position.value
            summary.compa_ratio = ratio
        items.append(summary)

    return PageOut(items=items, total=total, page=page, size=size)


@router.get("/{employee_no}", response_model=EmployeeDetailOut)
async def get_employee(employee_no: str) -> EmployeeDetailOut:
    employee = await repository.get(employee_no)
    if employee is None:
        raise HTTPException(status_code=404, detail=f"no employee {employee_no}")

    history = await repository.compensation_of(employee_no)
    detail = EmployeeDetailOut.of_employee(employee, history)

    bands = await load_bands()
    placement = place(bands, level=employee.level, country=employee.country, salary=history.current)
    if placement:
        position, ratio = placement
        detail.band_position = position.value
        detail.compa_ratio = ratio
    return detail


@router.post("/{employee_no}/raises", response_model=EmployeeDetailOut, status_code=201)
async def apply_raise(employee_no: str, request: RaiseIn) -> EmployeeDetailOut:
    try:
        history = await repository.apply_raise(
            employee_no,
            percent=request.percent,
            effective_from=request.effective_from,
            reason=request.reason,
        )
    except UnknownEmployee:
        raise HTTPException(status_code=404, detail=f"no employee {employee_no}") from None
    except InvalidCompensationChange as rejected:
        raise HTTPException(status_code=422, detail=str(rejected)) from None
    except ConcurrentChange as clashed:
        raise HTTPException(status_code=409, detail=str(clashed)) from None

    employee = await repository.get(employee_no)
    assert employee is not None
    return EmployeeDetailOut.of_employee(employee, history)

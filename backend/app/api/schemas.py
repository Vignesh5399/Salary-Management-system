"""Request and response shapes. Kept separate from the stored documents so the
wire format and the database can change independently."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

from app.domain.band import BandPosition
from app.domain.compensation import ChangeReason, CompensationHistory
from app.domain.money import Money
from app.persistence.models import Employee


class MoneyOut(BaseModel):
    amount: Decimal
    currency: str

    @staticmethod
    def of(money: Money) -> "MoneyOut":
        return MoneyOut(amount=money.amount, currency=money.currency.code)


class CompensationRecordOut(BaseModel):
    amount: MoneyOut
    effective_from: date
    effective_to: date | None
    reason: str


class EmployeeSummaryOut(BaseModel):
    employee_no: str
    name: str
    country: str
    department: str
    level: str
    job_title: str
    current_salary: MoneyOut
    band_position: str | None = None
    compa_ratio: Decimal | None = None

    @staticmethod
    def of(employee: Employee) -> "EmployeeSummaryOut":
        return EmployeeSummaryOut(
            employee_no=employee.employee_no,
            name=employee.name,
            country=employee.country,
            department=employee.department,
            level=employee.level,
            job_title=employee.job_title,
            current_salary=MoneyOut(
                amount=Money(
                    employee.current_amount_minor,
                    _currency(employee.current_currency),
                ).amount,
                currency=employee.current_currency,
            ),
        )


class EmployeeDetailOut(EmployeeSummaryOut):
    email: str
    hire_date: date
    history: list[CompensationRecordOut]

    @staticmethod
    def of_employee(employee: Employee, history: CompensationHistory) -> "EmployeeDetailOut":
        summary = EmployeeSummaryOut.of(employee)
        return EmployeeDetailOut(
            **summary.model_dump(),
            email=employee.email,
            hire_date=employee.hire_date.date(),
            history=[
                CompensationRecordOut(
                    amount=MoneyOut.of(record.amount),
                    effective_from=record.period.starts_on,
                    effective_to=record.period.ends_on,
                    reason=record.reason.value,
                )
                for record in history.records
            ],
        )


class PageOut(BaseModel):
    items: list[EmployeeSummaryOut]
    total: int
    page: int
    size: int


class RaiseIn(BaseModel):
    percent: Decimal = Field(gt=0, le=100)
    effective_from: date
    reason: ChangeReason = ChangeReason.MERIT


class GroupTotalOut(BaseModel):
    group: str
    headcount: int
    total_annual: MoneyOut


class SummaryOut(BaseModel):
    headcount: int
    total_annual: MoneyOut
    average_annual: MoneyOut
    below_band: int
    by_country: list[GroupTotalOut]
    by_department: list[GroupTotalOut]


def band_fields(position: BandPosition, ratio: Decimal) -> dict[str, object]:
    return {"band_position": position.value, "compa_ratio": ratio}


def _currency(code: str):  # noqa: ANN202 - trivial re-export to avoid a circular import
    from app.domain.currency import Currency

    return Currency.of(code)

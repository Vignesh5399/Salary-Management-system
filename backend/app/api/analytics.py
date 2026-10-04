"""One summary endpoint: what the organisation pays, in one reporting currency."""

from decimal import Decimal

from fastapi import APIRouter

from app.api.schemas import GroupTotalOut, MoneyOut, SummaryOut
from app.config import settings
from app.domain.currency import Currency
from app.domain.exchange import ExchangeRate
from app.domain.money import Money
from app.persistence.models import Band, Rate
from app.persistence.repository import EmployeeRepository

router = APIRouter(prefix="/api/analytics", tags=["analytics"])
repository = EmployeeRepository()


async def _rates() -> dict[str, ExchangeRate]:
    reporting = settings.reporting_currency
    return {
        rate.base: ExchangeRate.of(
            rate.base, rate.quote, rate.rate, effective_from=rate.effective_from.date()
        )
        for rate in await Rate.find(Rate.quote == reporting).to_list()
    }


def _to_reporting(amount_minor: int, currency: str, rates: dict[str, ExchangeRate]) -> Money:
    reporting = settings.reporting_currency
    local = Money(amount_minor, Currency.of(currency))
    if currency == reporting:
        return local
    return rates[currency].convert(local)


async def _grouped(dimension: str, rates: dict[str, ExchangeRate]) -> list[GroupTotalOut]:
    totals: dict[str, tuple[int, Money]] = {}
    for row in await repository.payroll_by(dimension):
        group = row["_id"]["group"]
        converted = _to_reporting(row["total_minor"], row["_id"]["currency"], rates)
        headcount, running = totals.get(group, (0, Money.zero(settings.reporting_currency)))
        totals[group] = (headcount + row["headcount"], running + converted)

    return [
        GroupTotalOut(group=group, headcount=headcount, total_annual=MoneyOut.of(total))
        for group, (headcount, total) in sorted(totals.items())
    ]


@router.get("", response_model=SummaryOut)
async def summary() -> SummaryOut:
    rates = await _rates()
    by_country = await _grouped("country", rates)
    by_department = await _grouped("department", rates)

    headcount = sum(group.headcount for group in by_country)
    total = Money.zero(settings.reporting_currency)
    for group in by_country:
        total = total + Money.of(str(group.total_annual.amount), settings.reporting_currency)

    average = total * (Decimal(1) / Decimal(headcount)) if headcount else total
    below_band = await repository.count_below_band(await Band.find_all().to_list())

    return SummaryOut(
        headcount=headcount,
        total_annual=MoneyOut.of(total),
        average_annual=MoneyOut.of(average),
        below_band=below_band,
        by_country=by_country,
        by_department=by_department,
    )

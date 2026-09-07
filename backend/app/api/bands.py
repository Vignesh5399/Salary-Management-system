"""Loading bands and placing salaries in them.

Bands are a few dozen rows that change rarely, so they are read once per request
rather than joined per employee.
"""

from decimal import Decimal

from app.domain.band import BandPosition, SalaryBand
from app.domain.currency import Currency
from app.domain.money import Money
from app.persistence.models import Band


async def load_bands() -> dict[tuple[str, str], SalaryBand]:
    return {
        (band.level, band.country): SalaryBand(
            level=band.level,
            country=band.country,
            minimum=Money(band.minimum_minor, Currency.of(band.currency)),
            midpoint=Money(band.midpoint_minor, Currency.of(band.currency)),
            maximum=Money(band.maximum_minor, Currency.of(band.currency)),
        )
        for band in await Band.find_all().to_list()
    }


def place(
    bands: dict[tuple[str, str], SalaryBand],
    *,
    level: str,
    country: str,
    salary: Money,
) -> tuple[BandPosition, Decimal] | None:
    band = bands.get((level, country))
    if band is None:
        return None
    return band.position_of(salary), band.compa_ratio(salary)

"""Pay bands, and where a salary sits inside one."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from app.domain.money import Money


class InvalidBand(ValueError):
    """Raised when a band's bounds are not in order."""


class BandPosition(Enum):
    BELOW = "below"
    WITHIN = "within"
    ABOVE = "above"


@dataclass(frozen=True, slots=True)
class SalaryBand:
    """The pay range for one level in one country.

    Bounds are inclusive: a salary exactly at the minimum is in band. Bands are
    per country because the same level is worth different amounts in different
    markets, and a single global band would misreport every one of them.
    """

    level: str
    country: str
    minimum: Money
    midpoint: Money
    maximum: Money

    @staticmethod
    def of(
        *,
        level: str,
        country: str,
        minimum: str,
        midpoint: str,
        maximum: str,
        currency: str,
    ) -> SalaryBand:
        bounds = (
            Money.of(minimum, currency),
            Money.of(midpoint, currency),
            Money.of(maximum, currency),
        )
        low, mid, high = bounds
        if not low <= mid <= high:
            raise InvalidBand(f"{level}/{country} bounds are out of order: {low}, {mid}, {high}")
        return SalaryBand(level=level, country=country, minimum=low, midpoint=mid, maximum=high)

    def compa_ratio(self, salary: Money) -> Decimal:
        """Salary as a proportion of the band midpoint. 1.0 means paid at market."""
        self.midpoint.require_same_currency_as(salary)
        ratio = Decimal(salary.amount_minor) / Decimal(self.midpoint.amount_minor)
        return ratio.quantize(Decimal("0.001"))

    def position_of(self, salary: Money) -> BandPosition:
        if salary < self.minimum:
            return BandPosition.BELOW
        if salary > self.maximum:
            return BandPosition.ABOVE
        return BandPosition.WITHIN

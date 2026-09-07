"""Money as an immutable value object over integer minor units."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from functools import total_ordering

from app.domain.currency import Currency


def _resolve(currency: str | Currency) -> Currency:
    return Currency.of(currency) if isinstance(currency, str) else currency


class CurrencyMismatch(ValueError):
    """Raised when two amounts in different currencies are combined or compared."""


class PrecisionError(ValueError):
    """Raised when an amount carries more precision than its currency allows."""


@total_ordering
@dataclass(frozen=True, slots=True, eq=True)
class Money:
    """An amount of money, held as whole minor units.

    Floats are never accepted and never produced: a salary that drifts by a
    fraction of a cent per operation is a defect that only surfaces at scale.
    """

    amount_minor: int
    currency: Currency

    @staticmethod
    def of(amount: str | Decimal, currency: str | Currency) -> Money:
        if isinstance(amount, float):
            raise TypeError("Money cannot be built from a float; pass a str or Decimal")

        resolved = _resolve(currency)
        value = Decimal(amount)
        scaled = value.scaleb(resolved.exponent)

        if scaled != scaled.to_integral_value():
            raise PrecisionError(
                f"{value} is more precise than {resolved.code} allows "
                f"({resolved.exponent} decimal places)"
            )

        return Money(int(scaled), resolved)

    @staticmethod
    def zero(currency: str | Currency) -> Money:
        return Money(0, _resolve(currency))

    @property
    def amount(self) -> Decimal:
        """The value in major units, for display and serialisation."""
        return Decimal(self.amount_minor).scaleb(-self.currency.exponent)

    def _same_currency_as(self, other: Money) -> None:
        if self.currency != other.currency:
            raise CurrencyMismatch(
                f"cannot combine {self.currency.code} with {other.currency.code}"
            )

    def __add__(self, other: Money) -> Money:
        self._same_currency_as(other)
        return Money(self.amount_minor + other.amount_minor, self.currency)

    def __sub__(self, other: Money) -> Money:
        self._same_currency_as(other)
        return Money(self.amount_minor - other.amount_minor, self.currency)

    def __neg__(self) -> Money:
        return Money(-self.amount_minor, self.currency)

    def __mul__(self, factor: Decimal | int) -> Money:
        """Scale by a factor, rounding half up.

        Half up rather than half even because the usual caller is a percentage
        raise, and rounding against the employee is the wrong default.
        """
        if isinstance(factor, float):
            raise TypeError("scale Money by a Decimal or int, never a float")
        scaled = (Decimal(self.amount_minor) * Decimal(factor)).quantize(
            Decimal(1), rounding=ROUND_HALF_UP
        )
        return Money(int(scaled), self.currency)

    def __lt__(self, other: Money) -> bool:
        self._same_currency_as(other)
        return self.amount_minor < other.amount_minor

    def __str__(self) -> str:
        return f"{self.currency.code} {self.amount}"

    def __repr__(self) -> str:
        return f"Money.of('{self.amount}', '{self.currency.code}')"

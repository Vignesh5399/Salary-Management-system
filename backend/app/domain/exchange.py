"""Effective-dated conversion between currencies."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.domain.currency import Currency
from app.domain.money import Money
from app.domain.rounding import to_whole_minor_units


class InvalidRate(ValueError):
    """Raised when a rate could not describe a real conversion."""


class UnconvertibleCurrency(ValueError):
    """Raised when an amount is not in this rate's source currency."""


@dataclass(frozen=True, slots=True)
class ExchangeRate:
    """One unit of ``base`` expressed in ``quote``, from a given date.

    Rates are effective-dated because reports must not move. A payroll cost
    for last March is converted at March's rate, so re-running the report a
    year later gives the same number.
    """

    base: Currency
    quote: Currency
    rate: Decimal
    effective_from: date

    @staticmethod
    def of(base: str, quote: str, rate: str | Decimal, *, effective_from: date) -> ExchangeRate:
        if isinstance(rate, float):
            raise TypeError("exchange rates must be a str or Decimal, never a float")

        value = Decimal(rate)
        if value <= 0:
            raise InvalidRate(f"rate must be positive, got {value}")

        base_currency = Currency.of(base)
        quote_currency = Currency.of(quote)
        if base_currency == quote_currency:
            raise InvalidRate(f"{base} to {quote} is not a conversion")

        return ExchangeRate(base_currency, quote_currency, value, effective_from)

    def convert(self, amount: Money) -> Money:
        if amount.currency != self.base:
            raise UnconvertibleCurrency(
                f"rate converts {self.base.code}, not {amount.currency.code}"
            )

        # Scale through major units so that source and target exponents may differ.
        in_major = Decimal(amount.amount_minor).scaleb(-self.base.exponent)
        converted = (in_major * self.rate).scaleb(self.quote.exponent)

        return Money(to_whole_minor_units(converted), self.quote)

    def __str__(self) -> str:
        return f"1 {self.base.code} = {self.rate} {self.quote.code} from {self.effective_from}"

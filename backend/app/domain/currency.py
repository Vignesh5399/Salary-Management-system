"""Currencies, and how many minor units they subdivide into."""

from __future__ import annotations

from dataclasses import dataclass


class UnknownCurrency(ValueError):
    """Raised when a currency code is not one this system supports."""


@dataclass(frozen=True, slots=True)
class Currency:
    """An ISO 4217 currency and its minor-unit exponent.

    The exponent belongs to the currency, not to the amount: USD subdivides into
    100 cents, JPY does not subdivide at all. Holding it here means no other part
    of the system has to guess at a scale.
    """

    code: str
    exponent: int

    @staticmethod
    def of(code: str) -> Currency:
        try:
            return _REGISTRY[code]
        except KeyError:
            raise UnknownCurrency(f"unsupported currency: {code!r}") from None

    def __str__(self) -> str:
        return self.code


_REGISTRY: dict[str, Currency] = {
    currency.code: currency
    for currency in (
        Currency("USD", 2),
        Currency("EUR", 2),
        Currency("GBP", 2),
        Currency("INR", 2),
        Currency("SGD", 2),
        Currency("AUD", 2),
        Currency("JPY", 0),
    )
}

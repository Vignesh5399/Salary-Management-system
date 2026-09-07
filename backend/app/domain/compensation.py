"""An employee's pay over time, as a chain of effective-dated records."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, timedelta
from decimal import Decimal
from enum import Enum

from app.domain.money import Money
from app.domain.period import EffectivePeriod


class InvalidCompensationChange(ValueError):
    """Raised when a change would leave the history in an inconsistent state."""


class ChangeReason(Enum):
    """Why a salary changed. Recorded because 'what did this cost us' is asked by reason."""

    HIRE = "hire"
    MERIT = "merit"
    PROMOTION = "promotion"
    MARKET_ADJUSTMENT = "market_adjustment"


@dataclass(frozen=True, slots=True)
class CompensationRecord:
    """One salary, and the window over which it applied."""

    amount: Money
    period: EffectivePeriod
    reason: ChangeReason

    def closed_on(self, day: date) -> CompensationRecord:
        """A copy of this record, no longer in force after ``day``."""
        return replace(self, period=self.period.closing_on(day))


@dataclass(frozen=True, slots=True)
class CompensationHistory:
    """The full pay history for one employee.

    Append-only and immutable: every operation returns a new history. The
    records are held in chronological order with exactly one open at the end,
    which is what makes ``salary_on`` answerable for any past date.
    """

    records: tuple[CompensationRecord, ...]

    @staticmethod
    def starting_with(amount: Money, *, on: date) -> CompensationHistory:
        return CompensationHistory(
            (
                CompensationRecord(
                    amount=amount,
                    period=EffectivePeriod.opening_on(on),
                    reason=ChangeReason.HIRE,
                ),
            )
        )

    @property
    def _current_record(self) -> CompensationRecord:
        return self.records[-1]

    @property
    def current(self) -> Money:
        return self._current_record.amount

    def salary_on(self, day: date) -> Money | None:
        """What this employee was paid on ``day``, or None if they were not yet hired."""
        for record in self.records:
            if record.period.covers(day):
                return record.amount
        return None

    def raise_to(
        self, amount: Money, *, effective_from: date, reason: ChangeReason
    ) -> CompensationHistory:
        current = self._current_record
        self._reject_unless_applicable(amount, effective_from)

        successor = CompensationRecord(
            amount=amount,
            period=EffectivePeriod.opening_on(effective_from),
            reason=reason,
        )
        superseded = current.closed_on(effective_from - timedelta(days=1))

        return CompensationHistory((*self.records[:-1], superseded, successor))

    def _reject_unless_applicable(self, amount: Money, effective_from: date) -> None:
        current = self._current_record
        if amount.currency != current.amount.currency:
            raise InvalidCompensationChange(
                f"cannot change currency from {current.amount.currency.code} to "
                f"{amount.currency.code} as part of a pay change"
            )
        if effective_from <= current.period.starts_on:
            raise InvalidCompensationChange(
                f"a change effective {effective_from} would supersede a salary that "
                f"started {current.period.starts_on}"
            )

    def raise_by(
        self, percent: Decimal, *, effective_from: date, reason: ChangeReason
    ) -> CompensationHistory:
        """Apply a percentage increase, e.g. ``Decimal("5")`` for five percent."""
        multiplier = 1 + (percent / 100)
        return self.raise_to(
            self.current * multiplier, effective_from=effective_from, reason=reason
        )

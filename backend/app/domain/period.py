"""The window of time over which a value was in force."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date


class InvalidPeriod(ValueError):
    """Raised when a period would be malformed."""


@dataclass(frozen=True, slots=True)
class EffectivePeriod:
    """A date range with an inclusive end, or no end at all.

    ``ends_on`` is the last day the value applied, not the first day it stopped.
    That matches how the HR Manager reads a pay record, at the cost of making
    adjacency ``end + 1 day == next.start``.
    """

    starts_on: date
    ends_on: date | None = None

    @staticmethod
    def opening_on(day: date) -> EffectivePeriod:
        return EffectivePeriod(starts_on=day)

    @property
    def is_open(self) -> bool:
        return self.ends_on is None

    def closing_on(self, day: date) -> EffectivePeriod:
        """Return a copy of this period closed on ``day``. Does not mutate."""
        if not self.is_open:
            raise InvalidPeriod(f"period already ended on {self.ends_on}")
        if day < self.starts_on:
            raise InvalidPeriod(f"cannot end on {day}, before the start {self.starts_on}")
        return replace(self, ends_on=day)

    def covers(self, day: date) -> bool:
        if day < self.starts_on:
            return False
        return self.ends_on is None or day <= self.ends_on

    def overlaps(self, other: EffectivePeriod) -> bool:
        return self.starts_on <= other._last_day and other.starts_on <= self._last_day

    @property
    def _last_day(self) -> date:
        """The end, or the far future for an open period, so comparisons stay total."""
        return self.ends_on if self.ends_on is not None else date.max

    def __str__(self) -> str:
        return f"{self.starts_on} to {self.ends_on or 'present'}"

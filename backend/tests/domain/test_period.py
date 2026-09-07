from datetime import date

import pytest

from app.domain.period import EffectivePeriod, InvalidPeriod


def test_an_open_period_has_no_end() -> None:
    period = EffectivePeriod.opening_on(date(2024, 1, 1))

    assert period.is_open
    assert period.ends_on is None


def test_an_open_period_covers_its_first_day() -> None:
    period = EffectivePeriod.opening_on(date(2024, 1, 1))

    assert period.covers(date(2024, 1, 1))


def test_an_open_period_covers_any_later_day() -> None:
    period = EffectivePeriod.opening_on(date(2024, 1, 1))

    assert period.covers(date(2099, 12, 31))


def test_a_period_does_not_cover_days_before_it_started() -> None:
    period = EffectivePeriod.opening_on(date(2024, 1, 1))

    assert not period.covers(date(2023, 12, 31))


def test_a_closed_period_covers_its_final_day() -> None:
    # ends_on is inclusive: it is the last day the salary was in force,
    # which is how HR reads a payroll record.
    period = EffectivePeriod.opening_on(date(2024, 1, 1)).closing_on(date(2024, 6, 30))

    assert period.covers(date(2024, 6, 30))


def test_a_closed_period_does_not_cover_the_day_after_it_ended() -> None:
    period = EffectivePeriod.opening_on(date(2024, 1, 1)).closing_on(date(2024, 6, 30))

    assert not period.covers(date(2024, 7, 1))


def test_closing_a_period_leaves_the_original_untouched() -> None:
    original = EffectivePeriod.opening_on(date(2024, 1, 1))

    original.closing_on(date(2024, 6, 30))

    assert original.is_open


def test_a_period_cannot_end_before_it_starts() -> None:
    with pytest.raises(InvalidPeriod):
        EffectivePeriod.opening_on(date(2024, 6, 30)).closing_on(date(2024, 1, 1))


def test_a_period_may_start_and_end_on_the_same_day() -> None:
    period = EffectivePeriod.opening_on(date(2024, 1, 1)).closing_on(date(2024, 1, 1))

    assert period.covers(date(2024, 1, 1))


def test_a_closed_period_cannot_be_closed_again() -> None:
    period = EffectivePeriod.opening_on(date(2024, 1, 1)).closing_on(date(2024, 6, 30))

    with pytest.raises(InvalidPeriod):
        period.closing_on(date(2024, 9, 30))


def test_two_periods_covering_a_common_day_overlap() -> None:
    first = EffectivePeriod.opening_on(date(2024, 1, 1)).closing_on(date(2024, 6, 30))
    second = EffectivePeriod.opening_on(date(2024, 6, 30)).closing_on(date(2024, 12, 31))

    assert first.overlaps(second)
    assert second.overlaps(first)


def test_adjacent_periods_do_not_overlap() -> None:
    # The successor starts the day after its predecessor ends. This is the
    # shape every valid compensation history must have.
    first = EffectivePeriod.opening_on(date(2024, 1, 1)).closing_on(date(2024, 6, 30))
    second = EffectivePeriod.opening_on(date(2024, 7, 1))

    assert not first.overlaps(second)
    assert not second.overlaps(first)


def test_two_open_periods_always_overlap() -> None:
    first = EffectivePeriod.opening_on(date(2024, 1, 1))
    second = EffectivePeriod.opening_on(date(2030, 1, 1))

    assert first.overlaps(second)


def test_an_open_period_overlaps_a_closed_one_that_starts_later() -> None:
    open_period = EffectivePeriod.opening_on(date(2024, 1, 1))
    later = EffectivePeriod.opening_on(date(2025, 1, 1)).closing_on(date(2025, 6, 30))

    assert open_period.overlaps(later)

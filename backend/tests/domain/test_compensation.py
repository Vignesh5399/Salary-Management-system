from datetime import date
from decimal import Decimal

import pytest

from app.domain.compensation import (
    ChangeReason,
    CompensationHistory,
    InvalidCompensationChange,
)
from app.domain.money import Money

HIRED = date(2022, 4, 1)


def _inr(amount: str) -> Money:
    return Money.of(amount, "INR")


def _hired_on_100k() -> CompensationHistory:
    return CompensationHistory.starting_with(_inr("100000.00"), on=HIRED)


def test_a_new_history_holds_the_hire_salary() -> None:
    assert _hired_on_100k().current == _inr("100000.00")


def test_the_first_record_is_a_hire() -> None:
    history = _hired_on_100k()

    assert history.records[0].reason is ChangeReason.HIRE


def test_the_first_record_is_open() -> None:
    assert _hired_on_100k().records[0].period.is_open


def test_the_salary_is_known_from_the_hire_date() -> None:
    assert _hired_on_100k().salary_on(HIRED) == _inr("100000.00")


def test_the_salary_is_unknown_before_the_hire_date() -> None:
    assert _hired_on_100k().salary_on(date(2022, 3, 31)) is None


def test_a_raise_becomes_the_current_salary() -> None:
    history = _hired_on_100k().raise_to(
        _inr("120000.00"), effective_from=date(2023, 4, 1), reason=ChangeReason.MERIT
    )

    assert history.current == _inr("120000.00")


def test_a_raise_closes_the_previous_record_the_day_before_it_starts() -> None:
    history = _hired_on_100k().raise_to(
        _inr("120000.00"), effective_from=date(2023, 4, 1), reason=ChangeReason.MERIT
    )

    assert history.records[0].period.ends_on == date(2023, 3, 31)


def test_the_old_salary_is_still_returned_for_a_day_it_applied_to() -> None:
    history = _hired_on_100k().raise_to(
        _inr("120000.00"), effective_from=date(2023, 4, 1), reason=ChangeReason.MERIT
    )

    assert history.salary_on(date(2023, 3, 31)) == _inr("100000.00")


def test_the_new_salary_applies_from_the_day_it_took_effect() -> None:
    history = _hired_on_100k().raise_to(
        _inr("120000.00"), effective_from=date(2023, 4, 1), reason=ChangeReason.MERIT
    )

    assert history.salary_on(date(2023, 4, 1)) == _inr("120000.00")


def test_applying_a_raise_leaves_the_original_history_untouched() -> None:
    original = _hired_on_100k()

    original.raise_to(_inr("120000.00"), effective_from=date(2023, 4, 1), reason=ChangeReason.MERIT)

    assert original.current == _inr("100000.00")
    assert len(original.records) == 1


def test_a_raise_cannot_take_effect_before_the_current_salary_started() -> None:
    history = _hired_on_100k()

    with pytest.raises(InvalidCompensationChange):
        history.raise_to(
            _inr("120000.00"), effective_from=date(2022, 1, 1), reason=ChangeReason.MERIT
        )


def test_a_raise_cannot_take_effect_on_the_day_the_current_salary_started() -> None:
    # That would leave the superseded record covering no days at all.
    history = _hired_on_100k()

    with pytest.raises(InvalidCompensationChange):
        history.raise_to(_inr("120000.00"), effective_from=HIRED, reason=ChangeReason.MERIT)


def test_a_change_of_currency_is_not_a_raise() -> None:
    # Relocating someone to another country is a different operation with its
    # own band and FX questions. Rejecting it here keeps them from being conflated.
    history = _hired_on_100k()

    with pytest.raises(InvalidCompensationChange):
        history.raise_to(
            Money.of("2000.00", "USD"),
            effective_from=date(2023, 4, 1),
            reason=ChangeReason.MARKET_ADJUSTMENT,
        )


def test_a_percentage_raise_scales_the_current_salary() -> None:
    history = _hired_on_100k().raise_by(
        Decimal("5"), effective_from=date(2023, 4, 1), reason=ChangeReason.MERIT
    )

    assert history.current == _inr("105000.00")


def test_a_percentage_raise_records_the_reason_given() -> None:
    history = _hired_on_100k().raise_by(
        Decimal("15"), effective_from=date(2023, 4, 1), reason=ChangeReason.PROMOTION
    )

    assert history.records[-1].reason is ChangeReason.PROMOTION


def test_records_accumulate_in_chronological_order() -> None:
    history = (
        _hired_on_100k()
        .raise_by(Decimal("10"), effective_from=date(2023, 4, 1), reason=ChangeReason.MERIT)
        .raise_by(Decimal("10"), effective_from=date(2024, 4, 1), reason=ChangeReason.MERIT)
    )

    starts = [record.period.starts_on for record in history.records]
    assert starts == [HIRED, date(2023, 4, 1), date(2024, 4, 1)]


def test_exactly_one_record_is_open_however_many_raises_are_applied() -> None:
    history = (
        _hired_on_100k()
        .raise_by(Decimal("10"), effective_from=date(2023, 4, 1), reason=ChangeReason.MERIT)
        .raise_by(Decimal("10"), effective_from=date(2024, 4, 1), reason=ChangeReason.MERIT)
        .raise_by(Decimal("10"), effective_from=date(2025, 4, 1), reason=ChangeReason.MERIT)
    )

    assert sum(1 for record in history.records if record.period.is_open) == 1


def test_no_two_records_ever_overlap() -> None:
    history = (
        _hired_on_100k()
        .raise_by(Decimal("10"), effective_from=date(2023, 4, 1), reason=ChangeReason.MERIT)
        .raise_by(Decimal("10"), effective_from=date(2024, 4, 1), reason=ChangeReason.MERIT)
    )

    periods = [record.period for record in history.records]
    assert not any(a.overlaps(b) for i, a in enumerate(periods) for b in periods[i + 1 :])


def test_the_salary_for_every_day_since_hire_is_answerable() -> None:
    history = _hired_on_100k().raise_by(
        Decimal("10"), effective_from=date(2023, 4, 1), reason=ChangeReason.MERIT
    )

    assert history.salary_on(date(2022, 12, 25)) == _inr("100000.00")
    assert history.salary_on(date(2023, 4, 1)) == _inr("110000.00")
    assert history.salary_on(date(2026, 1, 1)) == _inr("110000.00")

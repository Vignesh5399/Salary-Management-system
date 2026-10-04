from decimal import Decimal

import pytest

from app.domain.currency import UnknownCurrency
from app.domain.money import CurrencyMismatch, Money, PrecisionError


def test_money_is_built_from_a_decimal_string_and_held_as_minor_units() -> None:
    salary = Money.of("1234.56", "USD")

    assert salary.amount_minor == 123456
    assert salary.amount == Decimal("1234.56")
    assert salary.currency.code == "USD"


def test_two_amounts_in_the_same_currency_can_be_added() -> None:
    assert Money.of("100.00", "USD") + Money.of("50.00", "USD") == Money.of("150.00", "USD")


def test_two_amounts_in_the_same_currency_can_be_subtracted() -> None:
    assert Money.of("100.00", "USD") - Money.of("50.00", "USD") == Money.of("50.00", "USD")


def test_adding_different_currencies_is_rejected() -> None:
    with pytest.raises(CurrencyMismatch):
        Money.of("100.00", "USD") + Money.of("100.00", "INR")


def test_subtracting_different_currencies_is_rejected() -> None:
    with pytest.raises(CurrencyMismatch):
        Money.of("100.00", "USD") - Money.of("100.00", "INR")


def test_a_percentage_raise_scales_the_amount() -> None:
    current = Money.of("1000.00", "USD")

    assert current * Decimal("1.035") == Money.of("1035.00", "USD")


def test_scaling_rounds_half_up_at_the_boundary() -> None:
    # 0.01 * 2.5 = 0.025, which is exactly half a cent. Banker's rounding would
    # give 0.02; a raise should never round against the employee.
    assert Money.of("0.01", "USD") * Decimal("2.5") == Money.of("0.03", "USD")


def test_currencies_without_minor_units_are_supported() -> None:
    salary = Money.of("1500", "JPY")

    assert salary.amount_minor == 1500
    assert salary.amount == Decimal("1500")


def test_input_more_precise_than_the_currency_allows_is_rejected() -> None:
    # Silently rounding a figure someone typed is how salary data drifts.
    with pytest.raises(PrecisionError):
        Money.of("10.005", "USD")


def test_floats_are_rejected_outright() -> None:
    with pytest.raises(TypeError):
        Money.of(10.5, "USD")  # type: ignore[arg-type]


def test_unknown_currency_codes_are_rejected() -> None:
    with pytest.raises(UnknownCurrency):
        Money.of("1.00", "XYZ")


def test_amounts_in_the_same_currency_can_be_ordered() -> None:
    assert Money.of("100.00", "USD") < Money.of("200.00", "USD")
    assert Money.of("200.00", "USD") > Money.of("100.00", "USD")


def test_ordering_different_currencies_is_rejected() -> None:
    with pytest.raises(CurrencyMismatch):
        _ = Money.of("100.00", "USD") < Money.of("100.00", "INR")


def test_equal_amounts_in_different_currencies_are_not_equal() -> None:
    assert Money.of("100.00", "USD") != Money.of("100.00", "INR")


def test_money_renders_with_its_currency() -> None:
    assert str(Money.of("1234.56", "USD")) == "USD 1234.56"
    assert str(Money.of("1500", "JPY")) == "JPY 1500"

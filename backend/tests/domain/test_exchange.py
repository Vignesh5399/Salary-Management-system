from datetime import date

import pytest

from app.domain.exchange import ExchangeRate, InvalidRate, UnconvertibleCurrency
from app.domain.money import Money


def _usd_to_inr(rate: str) -> ExchangeRate:
    return ExchangeRate.of("USD", "INR", rate, effective_from=date(2024, 1, 1))


def test_a_rate_converts_into_the_target_currency() -> None:
    converted = _usd_to_inr("83.00").convert(Money.of("100.00", "USD"))

    assert converted == Money.of("8300.00", "INR")


def test_conversion_rounds_half_up_to_the_target_minor_units() -> None:
    # 1.00 USD at 83.455 is 83.455 INR, exactly half a paisa.
    converted = _usd_to_inr("83.455").convert(Money.of("1.00", "USD"))

    assert converted == Money.of("83.46", "INR")


def test_conversion_respects_a_target_currency_with_no_minor_units() -> None:
    rate = ExchangeRate.of("USD", "JPY", "150.40", effective_from=date(2024, 1, 1))

    assert rate.convert(Money.of("10.00", "USD")) == Money.of("1504", "JPY")


def test_conversion_from_a_currency_with_no_minor_units() -> None:
    rate = ExchangeRate.of("JPY", "USD", "0.0067", effective_from=date(2024, 1, 1))

    assert rate.convert(Money.of("100000", "JPY")) == Money.of("670.00", "USD")


def test_converting_the_wrong_currency_is_rejected() -> None:
    with pytest.raises(UnconvertibleCurrency):
        _usd_to_inr("83.00").convert(Money.of("100.00", "GBP"))


def test_a_zero_rate_is_rejected() -> None:
    with pytest.raises(InvalidRate):
        _usd_to_inr("0")


def test_a_negative_rate_is_rejected() -> None:
    with pytest.raises(InvalidRate):
        _usd_to_inr("-83.00")


def test_a_rate_between_a_currency_and_itself_is_rejected() -> None:
    with pytest.raises(InvalidRate):
        ExchangeRate.of("USD", "USD", "1.00", effective_from=date(2024, 1, 1))


def test_a_rate_built_from_a_float_is_rejected() -> None:
    with pytest.raises(TypeError):
        ExchangeRate.of("USD", "INR", 83.0, effective_from=date(2024, 1, 1))  # type: ignore[arg-type]


def test_converting_zero_yields_zero_in_the_target_currency() -> None:
    assert _usd_to_inr("83.00").convert(Money.zero("USD")) == Money.zero("INR")


def test_a_rate_knows_when_it_took_effect() -> None:
    rate = _usd_to_inr("83.00")

    assert rate.effective_from == date(2024, 1, 1)


def test_rates_with_the_same_terms_are_equal() -> None:
    assert _usd_to_inr("83.00") == _usd_to_inr("83.00")


def test_rates_with_different_values_are_not_equal() -> None:
    assert _usd_to_inr("83.00") != _usd_to_inr("84.00")

from decimal import Decimal

import pytest

from app.domain.band import BandPosition, InvalidBand, SalaryBand
from app.domain.money import CurrencyMismatch, Money


def _band() -> SalaryBand:
    return SalaryBand.of(
        level="L4",
        country="IN",
        minimum="1000000.00",
        midpoint="1250000.00",
        maximum="1500000.00",
        currency="INR",
    )


def _inr(amount: str) -> Money:
    return Money.of(amount, "INR")


def test_a_band_cannot_have_a_midpoint_below_its_minimum() -> None:
    with pytest.raises(InvalidBand):
        SalaryBand.of(
            level="L4",
            country="IN",
            minimum="1250000.00",
            midpoint="1000000.00",
            maximum="1500000.00",
            currency="INR",
        )


def test_a_band_cannot_have_a_maximum_below_its_midpoint() -> None:
    with pytest.raises(InvalidBand):
        SalaryBand.of(
            level="L4",
            country="IN",
            minimum="1000000.00",
            midpoint="1500000.00",
            maximum="1250000.00",
            currency="INR",
        )


def test_the_midpoint_has_a_compa_ratio_of_one() -> None:
    assert _band().compa_ratio(_inr("1250000.00")) == Decimal("1.000")


def test_a_salary_below_the_midpoint_has_a_compa_ratio_below_one() -> None:
    assert _band().compa_ratio(_inr("1000000.00")) == Decimal("0.800")


def test_a_salary_above_the_midpoint_has_a_compa_ratio_above_one() -> None:
    assert _band().compa_ratio(_inr("1500000.00")) == Decimal("1.200")


def test_a_compa_ratio_is_reported_to_three_decimal_places() -> None:
    assert _band().compa_ratio(_inr("1111111.00")) == Decimal("0.889")


def test_a_compa_ratio_cannot_be_taken_across_currencies() -> None:
    with pytest.raises(CurrencyMismatch):
        _band().compa_ratio(Money.of("50000.00", "USD"))


def test_a_salary_under_the_minimum_is_below_band() -> None:
    assert _band().position_of(_inr("900000.00")) is BandPosition.BELOW


def test_a_salary_over_the_maximum_is_above_band() -> None:
    assert _band().position_of(_inr("1600000.00")) is BandPosition.ABOVE


def test_a_salary_inside_the_range_is_within_band() -> None:
    assert _band().position_of(_inr("1250000.00")) is BandPosition.WITHIN


def test_the_minimum_itself_is_within_band() -> None:
    assert _band().position_of(_inr("1000000.00")) is BandPosition.WITHIN


def test_the_maximum_itself_is_within_band() -> None:
    assert _band().position_of(_inr("1500000.00")) is BandPosition.WITHIN


def test_a_band_is_identified_by_level_and_country() -> None:
    # Pay for the same level differs by market, so the band is per country.
    band = _band()

    assert (band.level, band.country) == ("L4", "IN")

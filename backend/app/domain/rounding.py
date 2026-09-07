"""The single place this system decides how fractions of a minor unit resolve."""

from decimal import ROUND_HALF_UP, Decimal


def to_whole_minor_units(value: Decimal) -> int:
    """Round to a whole minor unit, half away from zero.

    Half up rather than half even: the callers are percentage raises and
    currency conversion, and rounding against the employee is the wrong
    default for both.
    """
    return int(value.quantize(Decimal(1), rounding=ROUND_HALF_UP))

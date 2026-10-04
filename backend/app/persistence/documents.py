"""Mapping between the compensation aggregate and its stored document form.

Deliberately free of any MongoDB dependency: these are pure functions over
dictionaries, so they run in the fast suite and the driver is only responsible
for moving those dictionaries in and out.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, date, datetime
from itertools import pairwise
from typing import Any

from app.domain.compensation import (
    ChangeReason,
    CompensationHistory,
    CompensationRecord,
)
from app.domain.currency import Currency, UnknownCurrency
from app.domain.money import Money
from app.domain.period import EffectivePeriod


class MalformedDocument(ValueError):
    """Raised when stored documents cannot form a valid compensation history."""


def compensation_to_documents(history: CompensationHistory) -> list[dict[str, Any]]:
    return [_record_to_document(record) for record in history.records]


def compensation_from_documents(
    documents: Sequence[Mapping[str, Any]],
) -> CompensationHistory:
    if not documents:
        raise MalformedDocument("an employee with no compensation records is not valid")

    records = tuple(_record_from_document(document) for document in documents)
    _reject_unless_a_valid_chain(records)
    return CompensationHistory(records)


def _record_to_document(record: CompensationRecord) -> dict[str, Any]:
    return {
        "amount_minor": record.amount.amount_minor,
        "currency": record.amount.currency.code,
        "effective_from": _to_bson_datetime(record.period.starts_on),
        "effective_to": _to_bson_datetime(record.period.ends_on),
        "reason": record.reason.value,
    }


def _record_from_document(document: Mapping[str, Any]) -> CompensationRecord:
    try:
        amount = Money(int(document["amount_minor"]), Currency.of(document["currency"]))
        reason = ChangeReason(document["reason"])
        starts_on = _from_bson_datetime(document["effective_from"])
        ends_on = _from_bson_datetime(document["effective_to"])
    except KeyError as missing:
        raise MalformedDocument(f"compensation record is missing {missing}") from None
    except (UnknownCurrency, ValueError) as invalid:
        raise MalformedDocument(f"compensation record is not readable: {invalid}") from None

    period = EffectivePeriod(starts_on=starts_on, ends_on=ends_on)
    return CompensationRecord(amount=amount, period=period, reason=reason)


def _reject_unless_a_valid_chain(records: Sequence[CompensationRecord]) -> None:
    """Re-check what a partial unique index would have guaranteed in a relational store."""
    open_records = [record for record in records if record.period.is_open]
    if len(open_records) != 1:
        raise MalformedDocument(f"exactly one record must be current, found {len(open_records)}")
    if not records[-1].period.is_open:
        raise MalformedDocument("the current record must be the last one")

    for earlier, later in pairwise(records):
        if earlier.period.starts_on >= later.period.starts_on:
            raise MalformedDocument("compensation records are not in chronological order")
        if earlier.period.overlaps(later.period):
            raise MalformedDocument("compensation records overlap")


def _to_bson_datetime(day: date | None) -> datetime | None:
    """BSON has no date type, so dates are widened to midnight UTC."""
    if day is None:
        return None
    return datetime(day.year, day.month, day.day, tzinfo=UTC)


def _from_bson_datetime(value: datetime | None) -> date | None:
    """Narrow back to a date. PyMongo returns naive UTC datetimes by default."""
    if value is None:
        return None
    return value.date()

from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from app.domain.compensation import ChangeReason, CompensationHistory
from app.domain.money import Money
from app.persistence.documents import (
    MalformedDocument,
    compensation_from_documents,
    compensation_to_documents,
)

HIRED = date(2022, 4, 1)
RAISED = date(2023, 4, 1)


def _history() -> CompensationHistory:
    return CompensationHistory.starting_with(Money.of("100000.00", "INR"), on=HIRED).raise_by(
        Decimal("10"), effective_from=RAISED, reason=ChangeReason.MERIT
    )


def test_each_record_becomes_one_document() -> None:
    assert len(compensation_to_documents(_history())) == 2


def test_the_amount_is_stored_as_whole_minor_units() -> None:
    first = compensation_to_documents(_history())[0]

    assert first["amount_minor"] == 10000000
    assert isinstance(first["amount_minor"], int)


def test_the_currency_is_stored_as_its_code() -> None:
    assert compensation_to_documents(_history())[0]["currency"] == "INR"


def test_the_reason_is_stored_as_its_value() -> None:
    documents = compensation_to_documents(_history())

    assert documents[0]["reason"] == "hire"
    assert documents[1]["reason"] == "merit"


def test_dates_are_stored_as_datetimes() -> None:
    # BSON has no date type. Storing a date raises in the driver, so the
    # mapper widens to datetime rather than leaving it to fail at insert.
    first = compensation_to_documents(_history())[0]

    assert isinstance(first["effective_from"], datetime)


def test_dates_are_stored_at_midnight_utc() -> None:
    first = compensation_to_documents(_history())[0]

    assert first["effective_from"] == datetime(2022, 4, 1, tzinfo=UTC)


def test_an_open_record_stores_a_null_end() -> None:
    assert compensation_to_documents(_history())[-1]["effective_to"] is None


def test_a_closed_record_stores_its_final_day() -> None:
    first = compensation_to_documents(_history())[0]

    assert first["effective_to"] == datetime(2023, 3, 31, tzinfo=UTC)


def test_a_history_survives_a_round_trip_unchanged() -> None:
    original = _history()

    restored = compensation_from_documents(compensation_to_documents(original))

    assert restored == original


def test_a_round_trip_preserves_answers_about_past_dates() -> None:
    restored = compensation_from_documents(compensation_to_documents(_history()))

    assert restored.salary_on(date(2022, 12, 25)) == Money.of("100000.00", "INR")
    assert restored.salary_on(RAISED) == Money.of("110000.00", "INR")


def test_naive_datetimes_are_read_back_correctly() -> None:
    # PyMongo returns naive UTC datetimes unless configured otherwise.
    documents = compensation_to_documents(_history())
    naive = [
        {**doc, "effective_from": doc["effective_from"].replace(tzinfo=None)} for doc in documents
    ]

    assert compensation_from_documents(naive) == _history()


def test_an_empty_document_list_is_rejected() -> None:
    with pytest.raises(MalformedDocument):
        compensation_from_documents([])


def test_an_unrecognised_reason_is_rejected() -> None:
    documents = compensation_to_documents(_history())
    documents[0]["reason"] = "vibes"

    with pytest.raises(MalformedDocument):
        compensation_from_documents(documents)


def test_an_unrecognised_currency_is_rejected() -> None:
    documents = compensation_to_documents(_history())
    documents[0]["currency"] = "XYZ"

    with pytest.raises(MalformedDocument):
        compensation_from_documents(documents)


def test_a_missing_field_is_rejected() -> None:
    documents = compensation_to_documents(_history())
    del documents[0]["amount_minor"]

    with pytest.raises(MalformedDocument):
        compensation_from_documents(documents)


def test_documents_with_no_open_record_are_rejected() -> None:
    # The invariant the database will not enforce for us: something must be current.
    documents = compensation_to_documents(_history())
    documents[-1]["effective_to"] = datetime(2024, 1, 1, tzinfo=UTC)

    with pytest.raises(MalformedDocument):
        compensation_from_documents(documents)


def test_documents_with_overlapping_records_are_rejected() -> None:
    documents = compensation_to_documents(_history())
    documents[0]["effective_to"] = datetime(2023, 6, 30, tzinfo=UTC)

    with pytest.raises(MalformedDocument):
        compensation_from_documents(documents)


def test_documents_out_of_chronological_order_are_rejected() -> None:
    documents = list(reversed(compensation_to_documents(_history())))

    with pytest.raises(MalformedDocument):
        compensation_from_documents(documents)

# Design Notes

## Shape of the system

```mermaid
flowchart TB
    UI["Next.js UI<br/>directory · employee · analytics · exceptions"]
    API["FastAPI routers<br/>request/response schemas only"]
    SVC["Services<br/>orchestration, transactions"]
    DOM["Domain<br/>Money · EffectivePeriod · ExchangeRate<br/>CompensationHistory"]
    REPO["Repositories<br/>SQLAlchemy"]
    DB[("SQLite")]

    UI --> API --> SVC --> DOM
    SVC --> REPO --> DB
    REPO -.reconstitutes.-> DOM
```

The domain layer imports nothing from FastAPI or SQLAlchemy. That is not
architectural decoration — it is why the 62 domain tests run in milliseconds
with no fixtures, which is what makes test-driving the design practical.

## The domain model

```mermaid
classDiagram
    class Money {
        +int amount_minor
        +Currency currency
        +of(str, str) Money
        +__add__() Money
        +__mul__(Decimal) Money
    }
    class Currency {
        +str code
        +int exponent
    }
    class EffectivePeriod {
        +date starts_on
        +date? ends_on
        +covers(date) bool
        +overlaps(EffectivePeriod) bool
        +closing_on(date) EffectivePeriod
    }
    class ExchangeRate {
        +Currency base
        +Currency quote
        +Decimal rate
        +date effective_from
        +convert(Money) Money
    }
    class CompensationRecord {
        +Money amount
        +EffectivePeriod period
        +ChangeReason reason
    }
    class CompensationHistory {
        +tuple~CompensationRecord~ records
        +current Money
        +salary_on(date) Money?
        +raise_to(...) CompensationHistory
    }

    Money --> Currency
    ExchangeRate --> Currency
    ExchangeRate ..> Money : converts
    CompensationRecord --> Money
    CompensationRecord --> EffectivePeriod
    CompensationHistory --> CompensationRecord
```

## The three decisions everything else follows from

**Salary is a chain, not a value.** `CompensationHistory` holds records in
chronological order with exactly one open. A raise closes its predecessor the
day before it starts. Nothing is ever edited in place. This is what makes
"what did we pay her in March" and "what did the April cycle cost" answerable
at all, and it is the reason a mutable `salary` column was never on the table.

**Money is an integer and knows its currency.** No floats anywhere, and adding
INR to USD raises rather than producing a plausible wrong number. The
minor-unit exponent lives on `Currency`, so JPY works without a special case.

**Rates are effective-dated.** A historic report converts at the rate that
applied then, so re-running last year's payroll cost gives the same figure it
gave last year.

## Persistence intent

The aggregate's invariant — one open record per employee, no overlaps — is
enforced twice on purpose:

- in the domain, where `raise_to` is the only way to add a record; and
- in the database, by a partial unique index on
  `(employee_id) WHERE effective_to IS NULL`.

The domain check gives a good error message. The index means a bug elsewhere,
a bad migration, or a hand-run `INSERT` cannot corrupt a pay history. Neither
is redundant with the other.

## Scale

10,000 employees at two to five records each is roughly 30,000 rows — small
enough that SQLite holds it in page cache and any query is fast. Server-side
pagination and the indexes exist because the *shape* should be right at
500,000, not because this dataset needs them. The point at which this design
changes is when analytics aggregates start scanning the whole compensation
table per request; the answer then is a materialised current-salary view
refreshed on write, not a different database.

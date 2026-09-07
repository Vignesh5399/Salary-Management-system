# Salary Management — Requirements

## Goal

Give ACME's HR Manager a single place to hold compensation data for ~10,000 employees
across multiple countries, replacing the current spreadsheet sprawl, and let her answer
questions about how the organisation pays people without exporting anything.

## The persona and her questions

I scoped this from the questions the HR Manager needs answered, not from a feature list.
Every screen exists to answer one of these:

1. *What do we pay this person, and what have we paid them over time?*
2. *What is our total payroll cost, by country, department and level?*
3. *Who is paid below the bottom of their band?* (retention and compliance risk)
4. *What did this raise cycle cost us?*
5. *Is pay consistent for people at the same level in the same country?*

Question 1 and 4 are the reason compensation is modelled as history rather than a
current value. That single decision drives most of the design.

## In scope

- **Employee directory** — 10,000 records, server-side pagination, filter by country,
  department, level and status, sort by name or current salary.
- **Compensation history** — every salary is an effective-dated record with a reason
  (hire, merit, promotion, market adjustment, correction). Records are append-only;
  a correction is a new record, never an edit. This makes "what did we pay her in
  March" answerable, which a mutable salary column cannot do.
- **Multi-currency** — salaries are held in local currency and normalised to a single
  reporting currency using the FX rate effective on the record's own date, so historic
  reports do not silently change when rates move.
- **Salary bands** — per level and country, with minimum, midpoint and maximum. Enables
  compa-ratio and out-of-band detection.
- **Compensation analytics** — headcount and payroll cost, median and quartiles by
  department / country / level, and an exceptions view listing employees outside band.
- **CSV export** — the persona's current tool is Excel; she will not stop needing it
  on day one.

## Deliberately out of scope

| Excluded | Reasoning |
|---|---|
| Authentication and RBAC | A real system needs both, but for a single-persona demo they add surface without exercising the interesting domain logic. The API is structured so an auth dependency slots in at the router layer. |
| Approval workflows for raises | Requires a second persona (approver) and a state machine. Doubles the domain for no additional insight into pay. |
| Payroll execution, tax, benefits, equity | A different bounded context with its own compliance rules. Mixing it in would blur the model. |
| Live FX rate feed | Rates are seeded as effective-dated rows. A live feed is an adapter swap, not a design change, and would make tests non-deterministic. |
| Performance ratings | Would justify *why* a raise happened; the system only needs to record *that* it did. |
| Bulk raise cycles | Interesting, but the single-raise path proves the model. Batch is a loop over a solved problem. |

## Non-functional intent

- Money is never a float. Amounts are integers in minor units behind a `Money` value
  object that refuses to add different currencies.
- One open compensation record per employee, no overlapping periods, enforced by the
  database rather than by convention.
- Tests run in-memory with no network or containers, so the suite stays fast enough to
  drive development.
- 10,000 rows fits comfortably in memory; indexes and server-side paging are there to
  keep the shape correct at 500,000, not because SQLite struggles at this size.

## Success criteria

The HR Manager can answer all five questions above in under a minute each, and the
answer for a past date is still correct a year from now.

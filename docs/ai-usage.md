# Working with AI

The JD describes AI as a collaborator. I have treated it as a pairing partner:
it drafts, I review, and I keep the decisions. This file is the pairing record —
what I asked for, what came back, and where I disagreed.

Format: one entry per meaningful exchange. The rejections matter more than the
acceptances, so they are recorded in full.

---

## Session 1 — Database choice

**Considered:** MongoDB with FastAPI, on the grounds that the document model would
let me embed compensation history in the employee document and get atomic raises
without multi-document transactions. That argument is technically sound.

**Rejected.** Three reasons, in order of weight:

1. The brief specifies a relational database, and the JD names no database that
   would override it. Deviating from a stated constraint needs a stronger reason
   than "the alternative is also workable".
2. The core invariant — exactly one open compensation record per employee, with no
   overlapping periods — is a partial unique index in a relational store. In Mongo
   it becomes application discipline plus a schema validator, and I would be writing
   a tradeoffs document explaining how I compensated for a constraint I chose to
   give up.
3. Tests. In-memory SQLite gives a fresh database per test in milliseconds.
   MongoDB needs a container, which is slower and less deterministic — and a slow
   suite quietly erodes the TDD cycle this whole exercise is built on.

**Decision:** SQLAlchemy 2.0 + SQLite. Postgres is a `DATABASE_URL` change if the
data outgrows it; migrations are kept dialect-neutral so that stays true.

---

## Session 2 — Money representation

**Suggested:** store salary as `Decimal` with the currency code alongside it.

**Amended.** Decimal is correct about precision but says nothing about currency
safety — nothing stops `Decimal("100") + Decimal("100")` across INR and USD. I
asked instead for an immutable `Money` value object holding integer minor units
and a `Currency`, raising on mismatched arithmetic. Integer minor units also removes
the question of what the canonical scale is: JPY has none, most currencies have two,
and the currency itself should know.

**Kept:** the `ROUND_HALF_UP` policy for multiplication, which was suggested and is
right for percentage raises.

**Added by me:** `Money.of()` rejects input with more precision than the currency
allows, rather than rounding it silently. Rounding a user-entered figure without
telling them is how salary data quietly drifts. Multiplication must round; parsing
should not.

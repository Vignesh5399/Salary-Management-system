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

**Decision at the time:** SQLAlchemy 2.0 + SQLite.

**Reversed in session 5.** Left here unedited because a decision log that only
records the decisions that survived is not a log.

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

---

## Session 3 — Interval convention for compensation history

**Suggested:** half-open intervals (`[start, end)`), the usual default in
temporal modelling, where a record ending 2024-07-01 means the salary applied
up to but not including that day.

**Rejected.** The persona is an HR Manager reading a pay record, and to her
"this salary ended on 30 June" means 30 June was a day she paid it. Half-open
intervals are cleaner arithmetic but they push an off-by-one into every
conversation between the software and the person using it. I chose an
inclusive `ends_on`, and the successor period starts the following day.

The cost is that adjacency is `end + 1 day == next.start` rather than
`end == next.start`, which is one more thing the overlap test has to get right —
so there is an explicit test for exactly that case.

---

## Session 4 — Corrections, and what I chose not to build yet

**Suggested:** make the compensation history bitemporal — every record carries
both the period it applied to (valid time) and when it was entered (transaction
time), so a correction is a second record with the same effective date and a
later entry timestamp, and `salary_on()` resolves ties by whichever was recorded
most recently.

**Deferred, not rejected.** This is the correct model for "HR typed 50,000 when
it should have been 55,000", and that case is real. But it doubles the
resolution logic in the aggregate, and it needs an injectable clock to keep
tests deterministic. Neither is justified before the single-timeline case works.

I have taken the smaller step: the history is a chain in valid time only, and
`ChangeReason` has no CORRECTION member yet, because a reason code with no
supporting mechanism is worse than an honest gap. When corrections are built,
the change is additive — a `recorded_at` field and a tie-break in `salary_on()`.
The tests written now stay valid, which is the point of stopping here.

---

## Session 5 — Reversing the database decision

I went back to MongoDB. Recording this properly, because the reasoning in session 1
was sound on the evidence I had and two pieces of evidence changed.

**What changed.**

1. The domain layer was finished by this point, and `CompensationHistory` turned
   out to be a document — an ordered tuple, read and written whole, never queried
   record by record. When I wrote session 1 that was a guess. Now it is code I can
   look at, and the embedded-array argument I had dismissed applies to it directly.
2. The persistence layer had not been written yet, so the switch cost nothing. The
   domain imports no database library at all, which is the property that made
   changing my mind cheap. That was worth more here than being right first time.

**What did not change.** The brief still specifies a relational database, and
nothing in the JD overrides it. This is a deliberate deviation and it is documented
at the top of the requirements rather than in a footnote.

**The honest cost.** The one-open-record invariant loses its partial unique index
and is now defended by the aggregate, a collection-level JSON Schema validator, and
tests written specifically for it. Three mechanisms in place of one constraint. I
think the fit justifies it. I do not think it is free, and a reviewer who disagrees
with the trade is disagreeing with a judgement I have stated, not catching an
omission.

**Where AI helped and where it did not.** The embedded-array-plus-atomic-update
pattern came from the tool and is good. The reasons to reject it in session 1 were
also worth having. What neither the tool nor I could settle was how much the brief's
wording should weigh against engineering fit — that is a judgement call, it is mine,
and it is written down here so it can be argued with.

# The interleaving that double-books R7

## Before P09

Two requests can both pass the overlap pre-check before either saves:

| # | Maya's request | Omar's request | PostgreSQL state |
|---|---|---|---|
| 1 | `BEGIN` | | no confirmed R7 reservation |
| 2 | overlap query -> false | | unchanged |
| 3 | | `BEGIN` | unchanged |
| 4 | | overlap query -> false | Maya has not inserted yet |
| 5 | `INSERT R101` | | R101 is uncommitted and invisible to Omar |
| 6 | | `INSERT R102` | each transaction has a different row |
| 7 | `COMMIT` | | R101 is visible |
| 8 | | `COMMIT` | R101 and R102 overlap |

Both overlap answers were correct when read. The invariant still failed because
the check and insert were separate statements. This is **write skew**, not a
lost update: the requests insert different rows and overwrite nothing.

The invariant is:

> A room never has two Confirmed reservations covering the same night.

`SELECT ... FOR UPDATE` over matching reservations cannot repair this case.
The query returns no rows at the moment a free room is checked, and therefore
has nothing to lock.

## Repairs compared

| Repair | One process | Multiple processes | Cost |
|---|---|---|---|
| In-process lock | Correct | Broken | Very small, but the guarantee ends at the process boundary. |
| Guard row + `SELECT ... FOR UPDATE` | Correct | Correct | Contending bookings wait and every room needs a permanent guard row. |
| Optimistic guard-row version | Correct | Correct | No initial wait, but the loser detects zero updated rows and must retry. |
| Exclusion constraint | Correct | Correct | Adds a GiST write cost and works only for a rule expressible inside this table. |

The lesson's guard-row exercise observed a 0.91-second pessimistic wait. The
optimistic version did not wait; one transaction lost the compare-and-swap and
had to redo its work. Those are reference exercise measurements, not production
benchmarks for this repository.

## Repair kept

PostgreSQL now owns the invariant through `reservations_no_overlap`:

```sql
CONSTRAINT reservations_no_overlap EXCLUDE USING gist (
    room_number WITH =,
    daterange(check_in, check_out, '[)') WITH &&
) WHERE (status = 'Confirmed')
```

`btree_gist` supplies equality for the text room number. The half-open date
range matches the domain rule: a guest may arrive on another guest's checkout
date. Cancelled rows are excluded, so a cancelled stay blocks nothing.

The service keeps its pre-check for the ordinary readable response. If two
requests pass it together, PostgreSQL accepts one insert and refuses the other;
the store maps only SQLSTATE `23P01` on this named constraint to
`OverlapRejected`, and the API returns `409 Unavailable`.

## Verification

The in-memory race and automated HTTP concurrency test both finish with one
accepted booking and one refusal. The Docker/PostgreSQL run on 2026-11-14
produced:

```text
Maya -> 201 Created   {"reservationId":"R101","status":"Confirmed"}
Omar -> 409 Conflict  {"error":"Unavailable"}

Accepted responses: 1
CORRECT: one booking was accepted and one was refused.
```

The table then contained exactly one row. A direct overlapping `INSERT` for
13–15 November, bypassing the application, failed with:

```text
ERROR: conflicting key value violates exclusion constraint "reservations_no_overlap"
```

`tools/race_http.py` performs the same check against one API instance, or sends
Omar to a second URL to prove that the database rule crosses process boundaries.


# ADR-003: Protect the booking rule in PostgreSQL

- Status: accepted
- Date: 2026-11-14
- Extends: ADR-001 (modular monolith) and ADR-002 (availability cache)

## Context

The booking rule says that a room never has two Confirmed reservations covering
the same night. `BookingService.reserve` used to query for an overlap and then
insert. Concurrent requests could both read "free" and both insert. This is the
write-skew trace documented in `docs/interleaving.md`.

Repeatable Read does not stop it because neither request updates a row the other
read. Locking the matching reservation rows also cannot stop it when the query
matches no rows.

## Decision

Enforce the rule in PostgreSQL with a partial exclusion constraint:

```sql
CREATE EXTENSION IF NOT EXISTS btree_gist;

ALTER TABLE reservations
    ADD CONSTRAINT reservations_no_overlap
    EXCLUDE USING gist (
        room_number WITH =,
        daterange(check_in, check_out, '[)') WITH &&
    ) WHERE (status = 'Confirmed');
```

Keep the service pre-check for a cheap, readable ordinary-case response. The
constraint is the final authority. The PostgreSQL adapter maps only exclusion
violations from `reservations_no_overlap` to `OverlapRejected`; the service maps
that to the same `Unavailable` result and the API returns HTTP 409.

Reservation IDs come from the `reservation_ids` sequence. Counting rows could
give two concurrent requests the same ID and hide the overlap race behind a
primary-key violation.

## Alternatives considered

**An in-process lock.** Correct for one instance, but a second process owns a
different lock. Rejected because `docs/capacity.md` allows adding app instances.

**A guard row locked with `SELECT ... FOR UPDATE`.** Correct across instances,
but serializes bookings for a room and requires a permanent guard row for every
room. Prefer it when a future invariant cannot be expressed as a constraint.

**Optimistic guard-row versioning.** Correct and avoids waiting when contention
is rare. Rejected here because every writer must remember the compare-and-swap
and retry path, while the database can express this invariant directly.

**Serializable isolation.** Correct, but all affected transactions must handle
serialization failures and retries. This is broader than the one rule needs.

## Consequences

- Every writer, including a future endpoint, background job or direct SQL
  statement, is subject to the same rule.
- A concurrent insert may now fail with a constraint error; the adapter owns the
  translation to a domain error.
- Cancelled reservations do not block dates, and adjacent half-open stays do
  not overlap.
- Inserts maintain a GiST index and are slightly more expensive.
- The constraint only protects data contained in `reservations`; cross-table
  invariants need another strategy.
- Existing overlapping Confirmed rows must be resolved before adding the
  constraint to an old database volume.

## Revisit when

- another concurrency invariant cannot fit in one table;
- measured booking throughput shows GiST maintenance is material; or
- reservation writes move to more than one service.


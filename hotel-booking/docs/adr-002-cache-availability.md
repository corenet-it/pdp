# ADR-002: Cache room availability in Redis

- Status: accepted
- Date: 2026-11-07

## Context

Availability is the expected hot read path. Repeated date-range searches ask
PostgreSQL the same overlap question for every room, while the answer changes
only after a successful booking or cancellation. A cached answer can become
stale and must never be allowed to approve a booking.

## Decision

PostgreSQL remains the source of truth. Availability search uses cache-aside in
Redis with the key
`availability:v{version}:{checkIn}:{checkOut}` and a 30-second TTL.

On a miss the API reads PostgreSQL and stores the complete result under the
version observed before the read. On a successful reservation POST or DELETE,
the API increments `availability:version`; unsuccessful mutations leave it
unchanged. Old keys are not deleted eagerly and expire through their TTL.

Booking and cancellation never read availability from Redis. A reservation is
accepted or rejected from PostgreSQL state. Redis failures degrade search to a
database read instead of failing the business operation.

## Alternatives considered

- TTL only: simpler, but intentionally serves stale rooms for as long as 30
  seconds after every mutation.
- Delete date-specific keys: requires knowing every cached date range affected
  by a stay and is easy to get wrong.
- Write-through cache: couples the write path to Redis and still cannot replace
  PostgreSQL concurrency control.
- No cache: keeps the implementation small but repeats the dominant read work
  and does not address the capacity/energy hypothesis.

## Consequences

- Repeated searches avoid PostgreSQL after one miss, and invalidation is an
  O(1) version increment.
- Redis memory can contain unreachable old-version keys for at most 30 seconds.
- Search can be stale during a Redis outage until an already-cached value
  expires, but booking correctness remains in PostgreSQL.
- The first request for a new version/date range is still a database request;
  concurrent misses may create a cache stampede. Monitor this before adding a
  lock or request coalescing.
- This decision does not fix the existing concurrent booking race.

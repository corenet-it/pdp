# ADR-004 · Send confirmations with one bounded background worker

Accepted for the hotel-booking teaching application.

Email delivery spends most of its time waiting for I/O. A room already belongs
to its guest once PostgreSQL commits the reservation. Waiting for email on the
request path delays that acknowledgement and a delivery error can hide it.

## Decision

Keep a FIFO in each API process and run one sender thread. With a simulated
one-second delivery, eight waiting slots absorb a short burst and limit the
last accepted message's wait to roughly eight seconds under normal conditions.
If all slots are occupied, discard the new confirmation and count it. A delivery
exception increments the failure counter and the worker continues. Neither case
changes the booking result. A graceful stop closes intake and joins the worker.

## Other models considered

| Model | Reason for rejecting it here |
|---|---|
| Synchronous request handler | Each guest waits for the mail server. |
| Thread per email | A burst creates as many threads and concurrent sends as bookings. |
| Unbounded FIFO with one worker | Incoming mail can outpace delivery indefinitely, consuming memory and extending waits. |
| Process pool | Separate interpreters and serialization cost more for this I/O wait, and a pool still needs an admission limit. |
| Durable broker with independent consumers | Persistence and retries require more infrastructure and a way to coordinate the booking commit with publication. |

## Consequences

Mail is best effort. A forced stop loses pending messages and leaves the outcome
of an in-flight send unknown. There is also a gap between booking commit and
enqueue. Graceful shutdown can wait indefinitely for a hung sender. Each
replica has its own limit and counters. If guests must eventually receive every
confirmation, revisit a transactional outbox with retries and idempotent delivery.

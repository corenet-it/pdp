# ADR-001: Use a modular monolith for hotel booking

Status: Accepted, 31 October 2026

## Context

One small team builds and releases the app. P05 identifies Rooms, Reservations,
Payments and Notifications as separate business contexts. They need clear rule
owners and protected implementation details; there is no measured need for
separate releases or scaling yet.

S2 requires safe concurrent booking, S5 requires a booking to survive delivery
failure, and S6 requires local rule changes. The current check-then-save path
still double-books under the race demonstration; reorganising files cannot make
that operation atomic.

## Decision

Keep one Python application and deployment, split into four packages. Each
package exposes its contract through `__init__.py` and keeps concrete adapters
in `internal.py`. Reservations owns the booking rule. Notifications accepts its
own immutable Confirmation message rather than the Reservation domain object.
Payments exposes PaymentService and PaymentStatus with a simulated adapter; it
is not called by the booking flow yet.

`main.py` selects concrete adapters; tests may use them too. Three Import Linter
contracts protect all cross-module internal imports, keep Rooms independent,
and forbid Payments/Notifications from depending on Reservations. Run these
alongside the eight behaviour tests before accepting changes.

## Alternatives considered

| Option | Benefit | Cost / reason not selected |
|---|---|---|
| Keep the P04 structure | Minimal immediate work | Business boundaries stay unenforced; senders know Reservation |
| Separate services | Independent releases and scaling | Network failures, retries, distributed consistency, more deployments and monitoring without a measured need |
| Modular monolith (selected) | Explicit contracts with local calls and one deployment | All modules still release and scale together |

## Consequences

- Keep the same eight booking tests, nine demo lines and intentional race.
- S5 remains supported by saving before sending; no delivery retry is added.
- S6 gains executable boundary checks; Python privacy is a convention enforced
  by running lint, not an access restriction at runtime.
- S2 is still unmet: P09 must add database-level concurrency protection.
- State is in memory. Prices, maintenance, real payments and durable delivery
  remain future work; P05 descriptions do not implement those features.
- Boundary checks must be run consistently; CI integration is outside P06.

## Revisit when

A module has a measured independent release cadence, resource bottleneck or
availability requirement that outweighs distributed-system operating costs.
Record the evidence before extracting it into a separate service.

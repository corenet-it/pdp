# Quality scenarios

## Stakeholders

| Stakeholder | What they care about |
|---|---|
| Guest | Finding a suitable room, booking it without a clash, and receiving confirmation |
| Receptionist | Making and cancelling bookings quickly and seeing accurate availability |
| Hotel manager | Correct prices, deposits, room status, and reliable occupancy information |
| Payments team | Charging the right deposit and recording whether it was paid |
| Operations and maintenance | Taking rooms out of service without creating new bookings for them |
| Notification provider | Receiving complete confirmation requests and reporting delivery failures |
| Hotel owner | A system that remains dependable during busy booking periods and is easy to change |
| Developer and support team | Clear ownership of rules and useful diagnostics when something fails |

## Quality scenarios

### S1 · Availability is accurate

When a guest searches for a stay, the system returns the available rooms in **under
500 ms for a hotel with up to 10,000 rooms and 100,000 reservations**, and never
returns a room that has a confirmed overlapping reservation or is out of service.

### S2 · Concurrent booking is safe

When two guests try to book the same room for overlapping dates at the same time,
**at most one request succeeds**. The other receives `Unavailable`, and the data
contains no more than one confirmed reservation for that room and stay.

### S3 · Booking confirms quickly

For a valid request for a free room, the system returns a reservation id and saves
the reservation as `Confirmed` in **under 2 seconds in 95% of requests**.

### S4 · Payment failure is visible and safe

When a deposit cannot be authorised, the booking is **not reported as paid**;
the caller receives an explicit payment failure within **5 seconds**, and no
partially recorded payment can be mistaken for a successful deposit.

### S5 · Notification failure does not lose a booking

When the email or SMS provider is unavailable, the reservation remains saved with
its correct status, the operation reports `notification_failed`, and the failure
is logged or queued for retry within **5 seconds**.

### S6 · Rule changes stay local

When the hotel changes one business rule (for example, the Deluxe price or the
deposit percentage), **only the owning context and its tests need to change**;
the other three contexts continue to pass their existing tests without edits.


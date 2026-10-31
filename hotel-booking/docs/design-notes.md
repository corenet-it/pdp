## Why design before code

Low-level design decides which classes the system needs, what data each class stores, which methods it provides, and how the classes call each other.

## 2.1 User
- Data: id, name, email, age, role
- Methods: create(), update()

## 2.2 Room
- Data: id, name, price, status
- Methods: getDetails(), checkAvailability()

## 2.3 Booking
- Data: id, userId, roomId, startDate, endDate, status
- Methods: create(), cancel()

## 2.4 BookingService
- Methods: createBooking(), cancelBooking()
- Interactions: checks room availability and creates or cancels bookings.

# P04 design notes

These notes are reconstructed from the supplied P04 code; the original P03
notes above are retained. P03's User/Booking sketches correspond to the current
Guest/Reservation model. Proposed fields such as age, role, price and service
status are not present in the current app.

- BookingService depends on ReservationStore and NotificationSender protocols;
  main.py selects the in-memory store and simulated email sender.
- DateRange, Guest and Room are immutable values. Reservation owns Confirmed /
  Cancelled status, overlap blocking and cancellation.
- Notification errors are caught only after saving: acceptance and its id remain
  visible, with notification_failed=True.
- The six earlier behaviour examples are covered by the final eight P04 tests.
  The old Step2 file refers to the pre-refactoring concrete names and is kept
  only in the original source folder, not in this runnable project.
- Checking overlap and saving are separate operations. Refactoring preserves the
  race; it does not provide concurrent booking safety.

# P06 design notes

## Before

Checked on 31 October 2026 in the original P04 folder, with Python 3.11.9:

1. Tests: `python -m unittest -v` — 8 passed.
2. Demo: `python main.py` — the nine lines below, unchanged.
3. Race: `python main.py --race` — two Confirmed reservations, Double booking.

```text
Free rooms 12-14 Nov: R7, R8
Maya books R7 12-14 Nov: Accepted R101
Omar books R7 13-15 Nov: Unavailable
Nora books R7 14-16 Nov: Accepted R102
Omar books R8 15-15 Nov: InvalidDates
Free rooms 12-14 Nov: R8
Maya cancels R101: True
Free rooms 12-14 Nov: R7, R8
Confirmation emails sent: 2
```

```text
Maya and Omar both book R7 for 12-14 Nov at the same moment...
Maya: Accepted R101
Omar: Accepted R102
Confirmed reservations for R7 on 12-14 Nov: 2
Double booking! Both requests checked before either one saved.
```

## Modules

| Module | Public contract | Internal code |
|---|---|---|
| Rooms | Room, RoomCatalog | InMemoryRoomCatalog |
| Reservations | BookingService, BookingResult, Reservation, DateRange, Guest, ReservationStatus, ReservationStore | InMemoryReservationStore |
| Payments | PaymentStatus, PaymentService | SimulatedPaymentService |
| Notifications | Confirmation, NotificationSender | EmailNotificationSender, SmsNotificationSender |

Each package has an `__init__.py` contract. Reservations' booking/domain files
and Rooms' catalog file define the types re-exported by those contracts. The
root package contains only its docstring; it does not re-export all classes.

## Moves and wiring

The supplied P06 snapshot already contains the module moves. It is reused here
as the final code, together with P03/P05 documentation, rather than preserving
several conflicting copies of the app in the runnable folder.

1. Rooms owns Room and RoomCatalog; main.py creates InMemoryRoomCatalog and
   passes `CATALOG.all()` to BookingService. The service still accepts a list,
   preserving the supplied P04/P06 constructor behaviour.
2. Notifications has an immutable Confirmation containing exactly five fields:
   reservation id, guest email, room number, check-in and check-out. Its senders
   never import Reservation. The fake sender records confirmation.reservation_id.
3. Reservations owns the booking/domain/store code. Within its own module,
   internal code may use the domain classes directly.
4. Payments exposes a Decimal-based deposit protocol and Paid/Declined results.
   Its simulated adapter is available for tests/future wiring; the demo does not
   instantiate or call it. The integration is deferred to P17 in the source.
5. main.py imports the catalogue, reservation-store and email adapters.
   Tests may import adapters. Other modules use only public contracts.

The final suite keeps all eight original P04 test methods and their assertions;
only imports and the fake sender's Confirmation parameter/id access adapt.

## Three architecture checks

`pyproject.toml` contains three forbidden-import contracts:

1. **Modules do not import another module's internal code.** Every module is a
   source and every `internal.py` is protected; a module may use its own internals.
   This strengthens the supplied P06 check, which protected only imports made by
   Reservations. Main and tests are outside the hotel_booking graph.
2. **Rooms does not depend on any other module.**
3. **Payments and Notifications do not depend on Reservations.**

The configuration uses Import Linter's documented handling of overlapping
source/forbidden packages: own-module imports are allowed, cross-module imports
are rejected. See the [official forbidden-contract documentation](https://import-linter.readthedocs.io/en/stable/contract_types/forbidden/).
The checks guard Python import dependencies; they are not a runtime sandbox for
dynamic loading. No such loading is used by this project.

## Break it on purpose, then undo

Verified on a temporary copy of this project, without leaving a forbidden import
in the deliverable:

1. Add to `hotel_booking/reservations/booking.py`:

   ```python
   from hotel_booking.notifications.internal import EmailNotificationSender
   ```

2. Temporarily replace `self.notifications.send_confirmation(` with
   `EmailNotificationSender().send_confirmation(`.
3. Run `lint-imports --no-cache`. It exits with code 1 and reports:

   ```text
   Modules do not import another module's internal code BROKEN
   Rooms does not depend on any other module KEPT
   Payments and Notifications do not depend on Reservations KEPT

   Contracts: 2 kept, 1 broken.

   hotel_booking.reservations is not allowed to import
   hotel_booking.notifications.internal:

   - hotel_booking.reservations.booking -> hotel_booking.notifications.internal (l.8)
   ```

4. Remove the added import and restore `self.notifications.send_confirmation(`.
   Run lint again: `Contracts: 3 kept, 0 broken.`

Additional mutation checks attempted all 12 directed cross-module internal
imports (four modules × three foreign modules). Contract 1 rejected every one.
Separate public-import mutations from Rooms to Notifications, and from Payments
and Notifications to Reservations, were also rejected. Every mutation was undone.

## After

Final verification uses Python 3.11.9 and Import Linter 2.15:

```text
python -m unittest -v
Ran 8 tests
OK

lint-imports --no-cache
Modules do not import another module's internal code KEPT
Rooms does not depend on any other module KEPT
Payments and Notifications do not depend on Reservations KEPT
Contracts: 3 kept, 0 broken.
```

- The final demo is compared with P04 and with the nine expected lines above.
- The race still produces two accepted bookings and the same double-booking
  message. The scheduling demo uses sleeps as in P04; it is not a locking fix.
- The draw.io file retains the P03 **Use cases** page and adds **Context map**
  and **Modules**. Diagram arrows distinguish present calls/imports from planned
  business interactions.
- ADR-001 records the decision, alternatives, consequences and review triggers.
- requirements.md retains R1–R5 and appends R6 from the existing P04 behaviour.

## Remaining quality targets

S1/S3 latency and load targets are not benchmark results. S2 concurrent safety
is deliberately unmet. Real maintenance/pricing, the 30% policy, booking/payment
integration, durable state and delivery retries are outside P06. S5 is covered
for an immediate sender failure; S6 has the SMS example and import checks.

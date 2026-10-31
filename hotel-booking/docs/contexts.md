# Hotel business contexts

## Words

From R1–R6 and the P04/P06 code: hotel, guest, receptionist, Room, room number,
room type, Standard, Deluxe, catalogue, search, free, stay, DateRange, check-in,
check-out, night, overlap, book, reservation, reservation id, Accepted,
Unavailable, InvalidDates, Confirmed, Cancelled, cancel, view, store,
confirmation, guest email, email, SMS, sender, sent, notification_failed.

From the P05 business changes: operational availability, out of service,
maintenance, nightly price, deposit, 30%, amount, currency, payment,
authorisation, Paid, Declined, receipt, refund, delivery failure, retry.

The second group describes business responsibilities to preserve when the app
grows. It does not imply that prices, maintenance, refunds or retries have been
implemented in P06.

## Four contexts

### Rooms

**Job:** Own the hotel's room catalogue: identity, type and, when introduced,
nightly price and out-of-service periods. It answers which rooms the hotel offers.
It does not own reservations or decide whether a confirmed stay blocks a night.

**Words:** Room, room number, room type, Standard, Deluxe, catalogue, nightly
price, operational availability, out of service, maintenance.

**P06 public contract:** `Room(number, type)` and `RoomCatalog.all() -> list[Room]`.
`InMemoryRoomCatalog` is internal. Pricing and maintenance rules are design scope
only; the current catalogue lists rooms without dates or prices.

### Reservations

**Job:** Own stays, guests, booking acceptance, occupancy, cancellation and
lookup. Combine the Rooms catalogue with confirmed stays to answer a free-room
search. Save an accepted booking before requesting a confirmation.

**Words:** Guest, stay, DateRange, check-in, check-out, night, overlap, free,
reservation, reservation id, Accepted, Unavailable, InvalidDates, Confirmed,
Cancelled, cancel, view, store, notification_failed.

**P06 public contract:** `BookingService`, `BookingResult`, `Reservation`,
`DateRange`, `Guest`, `ReservationStatus`, `ReservationStore`.
`InMemoryReservationStore` is internal. Stays are half-open `[check_in, check_out)`.
The overlap check is sequential and is not atomic with saving: the race is
deliberately retained for P09.

### Payments

**Job:** Own deposit calculation, collection and payment outcomes; later own
payment records and refunds. It cannot change a reservation's lifecycle itself.

**Words:** Deposit, 30%, amount, currency, payment, authorisation, Paid, Declined,
receipt, refund.

**P06 public contract:** `PaymentService.take_deposit(reservation_id, amount)
-> PaymentStatus`, with `amount: Decimal` and `Paid`/`Declined` outcomes.
`SimulatedPaymentService` is internal: positive amounts are Paid, other amounts
are Declined. Booking does not call it yet; the supplied P06 contract reserves
that integration for P17. No 30% calculation or money transfer occurs in P06.

### Notifications

**Job:** Own message formatting, delivery channel and delivery outcome.
It receives a self-contained confirmation, never a `Reservation` object.
Reservations decides when to request the message; Notifications decides how to
send it. A delivery error cannot cancel a reservation.

**Words:** Confirmation, guest email, email, SMS, sender, sent, delivery failure,
retry.

**P06 public contract:** `Confirmation(reservation_id, guest_email, room_number,
check_in, check_out)` and `NotificationSender.send_confirmation(confirmation)`.
Email and SMS implementations are internal counters. A successful call returns
`None`; a failed call raises an exception. There is no delivery queue or retry
mechanism yet. The SMS sender uses the same teaching message; actual SMS delivery
would need a phone destination in an evolved contract.

## Same word, different meaning

| Word | Rooms | Reservations | Payments | Notifications |
|---|---|---|---|---|
| Room | Catalogue item identified by number and type | Reference to the room assigned to a stay | No room aggregate | Room number displayed in a message |
| Available / free | Operationally offered by the hotel | No overlapping Confirmed stay, and later also offered by Rooms | Not a payment status | Not a delivery status |
| Cancel | Withdraw a room from sale or remove a maintenance period; not a reservation transition | Keep the reservation as Cancelled and release its nights | A void/refund is a separate financial action | Stop a queued message only if a future delivery system supports it |
| Confirmed | No such Room status in the current code | Reservation exists and blocks its nights | Does not mean Paid | Does not mean Sent |
| Paid | Not a Room status | Not a ReservationStatus | Successful simulated deposit outcome | Not proof of message delivery |
| Sent | Not a Room status | Not proof of booking acceptance | Not proof of payment | In P06, the simulated sender incremented its counter; real delivery needs its own definition |
| Failed | Maintenance may make a room unavailable | InvalidDates or Unavailable rejects a request; notification_failed accompanies an accepted booking | Declined is the current payment failure result | Exception from the sender |

`Accepted` is a booking operation outcome; `Confirmed` is the stored reservation
status. Neither means `Paid` or `Sent`.

## Rule owners

These eight cards follow the supplied requirements and P05 business examples;
the prompt does not include a separate rule-card attachment. Each has one owner.

| Card | Owner | Reason and P06 status |
|---|---|---|
| 1. Offer only operational rooms, excluding maintenance periods | Rooms | Rooms owns service status; future capability |
| 2. Standard and Deluxe can have different nightly prices | Rooms | Room-type pricing belongs with the catalogue; future capability |
| 3. Check-out must be after check-in | Reservations | `DateRange.is_valid()` validates the stay before any save |
| 4. Accept a booking only if no Confirmed stay shares a night; save it and request one confirmation | Reservations | The booking rule spans checking, saving and requesting delivery. `reserve()` owns this orchestration; concurrent safety is still missing |
| 5. Cancellation keeps a Cancelled record and releases its nights | Reservations | `Reservation.cancel()` and `blocks()` own lifecycle and occupancy |
| 6. Collect a 30% deposit and record its outcome | Payments | Deposit policy and Paid/Declined belong to Payments; P06 provides only the simulation contract |
| 7. Deliver the requested confirmation through the configured channel | Notifications | Email/SMS formatting and delivery are sender responsibilities; P06 simulates both |
| 8. A delivery failure must not undo or hide an accepted booking | Reservations | `reserve()` catches sender errors after save and returns Accepted with notification_failed |

## Between contexts

Arrows on **Context map** show questions, commands and replies. Dashed arrows
are planned business messages. **Modules** shows current Python imports; a reply
or future event does not require a reverse import into Reservations.

| Arrow | Question, command or reply | Fields / response | P06 status |
|---|---|---|---|
| Reservations → Rooms | Question: “Which rooms can the hotel offer?” | No arguments; response `list[Room(number, type)]` | Wiring calls `RoomCatalog.all()` and passes its snapshot to BookingService; Reservations imports Room only |
| Rooms → Reservations | Planned announcement: `RoomOutOfService` | `room_number`, `from_date`, `to_date`, `reason` | Not implemented; later consumers must use a message, not import Reservations |
| Reservations → Payments | Command: “Take the deposit.” | `reservation_id: str`, `amount: Decimal` | Contract exists; not called by BookingService |
| Payments → Reservations | Reply to the deposit call | `PaymentStatus.PAID` or `PaymentStatus.DECLINED`; reservation id is known from the request | Contract exists; not called yet; not an event bus |
| Reservations → Notifications | Command: “Send this confirmation.” | `Confirmation`: `reservation_id`, `guest_email`, `room_number`, `check_in: date`, `check_out: date` | Implemented after saving the reservation |
| Notifications → Reservations | Delivery call result | `None` on success; exception on failure; caller maps it to `notification_failed=True` | Implemented as a return/exception, without a reverse module import |

Future room-offer queries may add stay dates, operational availability and nightly
price. Real payments may add payment id/currency and publish `DepositPaid` or
`DepositFailed`; durable notification delivery may publish `ConfirmationSent` or
`ConfirmationFailed`. These are possible contract extensions, not current fields.

## Context-map relationships

- Rooms, Payments and Notifications supply contracts to Reservations, which
  coordinates booking. The current Payments contract is reserved for later use.
- Rooms knows nothing about the other modules. Payments and Notifications do not
  import Reservations. No module may import another module's `internal.py`.
- No context writes another context's state. `main.py` composes the app and the
  tests may select internal implementations.

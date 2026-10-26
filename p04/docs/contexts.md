# Hotel business contexts

## Words from the requirements and code

Room, room number, Standard, Deluxe, price, available, out of service, stay,
check-in, check-out, night, guest, reservation, reservation id, book, cancel,
Confirmed, Cancelled, unavailable, overlap, free, deposit, payment, paid,
authorise, receipt, confirmation, email, SMS, sender, sent, failed, retry,
search, receptionist, hotel, notification.

## Four bounded contexts

### Rooms

**Job:** Maintain the hotel’s room catalogue and decide whether a room can be
offered for a requested stay. Rooms owns room number, room type, price, and
operational availability, including rooms taken out of service.

**Words:** Room, room number, Standard, Deluxe, price, available, out of service,
night.

### Reservations

**Job:** Turn a guest’s request into a reservation, prevent overlapping confirmed
stays, support cancellation, and answer reservation and availability queries.

**Words:** Guest, stay, check-in, check-out, reservation, reservation id, book,
cancel, Confirmed, Cancelled, unavailable, overlap, free.

### Payments

**Job:** Calculate and collect the deposit for a reservation and record the
payment outcome. Payments owns the meaning of `Paid`, not Reservations.

**Words:** Deposit, payment, paid, authorise, receipt, payment failed.

### Notifications

**Job:** Deliver confirmation messages through email or SMS and report delivery
success or failure. Notifications owns the meaning of `Sent`.

**Words:** Confirmation, email, SMS, sender, sent, failed, retry.

## Same word, different meaning

| Word | Rooms meaning | Reservations meaning | Payments meaning | Notifications meaning |
|---|---|---|---|---|
| **Room** | A catalogue item with a number, type, price, and service status | The room assigned to a particular stay | Not a payment object; it is only booking context | Not a message destination |
| **Cancel** | A room may be removed from service | A confirmed reservation becomes `Cancelled` and stops blocking dates | A payment may need a refund, but cancelling a reservation does not mean a payment was refunded | A queued message may be cancelled before delivery |
| **Confirmed** | A room is operationally available for sale | A reservation is accepted and blocks its nights | A payment authorisation may be confirmed separately | A message request was accepted by the sender, not necessarily delivered |
| **Paid** | No Rooms status | Not a reservation status; it is a payment result attached to a reservation | The deposit was successfully authorised and recorded | Not a delivery result |
| **Sent** | Not a Rooms concept | Not proof that a reservation exists | Not proof that a deposit was paid | The provider accepted or delivered a notification according to its delivery contract |

## Rule owners

| Rule card | Owner | Reason |
|---|---|---|
| 1. Only rooms that are operational and not out of service can be offered | Rooms | Operational room status and the room catalogue belong together |
| 2. Standard and Deluxe rooms have their own nightly prices | Rooms | Pricing is a property of the room type, not of a reservation |
| 3. Check-out must be after check-in | Reservations | A stay is part of a reservation and its date validity is needed before booking |
| 4. A room cannot have two overlapping `Confirmed` reservations | Reservations | Reservations owns occupancy and the meaning of `Confirmed` for a stay |
| 5. Cancelling a reservation makes its nights available again | Reservations | Only Reservations can change reservation lifecycle and occupancy |
| 6. A booking takes a 30% deposit and must record its payment outcome | Payments | Deposit calculation, authorisation, and `Paid` status are payment rules |
| 7. A successful booking requests a confirmation by email or SMS | Notifications | Delivery channel and message format belong to Notifications |
| 8. A failed notification must not undo an already saved booking | Reservations | Reservation acceptance is independent of delivery; Notifications reports failure |

## Between contexts

Arrows are intentionally expressed as questions or events. A context does not
reach into another context’s data.

| From → to | Contract | Fields |
|---|---|---|
| Reservations → Rooms | **Question:** “Can this room be offered for these dates, and what is its nightly price?” | `room_number`, `room_type`, `check_in`, `check_out`; response: `available`, `nightly_price` |
| Rooms → Reservations | **Event:** `RoomOutOfService` | `room_number`, `from`, `to`, `reason` |
| Reservations → Payments | **Command:** “Take the deposit for this reservation.” | `reservation_id`, `guest_id`, `amount`, `currency`, `due_at` |
| Payments → Reservations | **Event:** `DepositPaid` or `DepositFailed` | `reservation_id`, `payment_id`, `amount`, `currency`, `status`, `failure_reason` |
| Reservations → Notifications | **Command:** “Send a reservation confirmation.” | `reservation_id`, `guest_name`, `guest_email`, `room_number`, `check_in`, `check_out`, `status` |
| Notifications → Reservations | **Event:** `ConfirmationSent` or `ConfirmationFailed` | `reservation_id`, `channel`, `message_id`, `sent_at`, `failure_reason` |

## Context-map relationships

- **Reservations depends on Rooms** for room availability, service status, and
  price; Rooms publishes `RoomOutOfService`.
- **Reservations depends on Payments** for the deposit result; Payments
  publishes `DepositPaid` or `DepositFailed`.
- **Reservations depends on Notifications** only to request delivery;
  Notifications publishes the delivery result.
- No context shares tables or changes another context’s status directly.


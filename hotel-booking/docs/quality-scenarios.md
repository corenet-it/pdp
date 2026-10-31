# Quality scenarios

## Stakeholders

| Stakeholder | Interest |
|---|---|
| Guest | Suitable rooms, an unambiguous booking result, confirmation |
| Receptionist | Fast searches, booking lookup and cancellation |
| Hotel manager / owner | Correct occupancy, room prices, deposits and manageable operating costs |
| Maintenance team | Taking rooms out of service without new bookings for them |
| Payments team | Correct deposit amounts and visible payment outcomes |
| Notification provider / support | Complete messages and observable delivery errors |
| Developer / operations team | Local rule changes, clear boundaries and repeatable checks |

## S1 · Accurate and responsive search

- **Source / stimulus:** A guest or receptionist searches for a stay.
- **Environment / artifact:** Normal operation; room catalogue and reservation search,
  up to 10,000 rooms and 100,000 reservations.
- **Response:** List only rooms offered by Rooms with no overlapping Confirmed stay.
- **Measure:** 100% correct results against a prepared occupancy/maintenance dataset;
  p95 response time below 500 ms over 1,000 searches.
- **P06 evidence / gap:** Demo verifies occupancy changes for R7/R8. No load benchmark,
  maintenance model or performance guarantee has been implemented.

## S2 · Safe concurrent booking

- **Source / stimulus:** Two guests request the same room for overlapping nights.
- **Environment / artifact:** Concurrent requests; reservation check-and-save path.
- **Response:** Accept one request, reject the other as Unavailable, keep at most one
  Confirmed reservation for each room/night.
- **Measure:** In 1,000 paired attempts on initially free room/date combinations,
  exactly one acceptance per pair and zero overlapping Confirmed records.
- **P06 evidence / gap:** Sequential overlap tests pass. `python main.py --race`
  deliberately produces two accepted bookings. This target is not met in P06;
  database concurrency protection belongs to P09.

## S3 · Timely booking result

- **Source / stimulus:** A guest submits valid dates for a free room.
- **Environment / artifact:** Normal operation; BookingService and its store,
  healthy dependencies, 20 concurrent clients.
- **Response:** Save a Confirmed reservation and return Accepted with its id.
- **Measure:** p95 below 2 seconds over 1,000 valid requests; every returned id
  resolves to a saved reservation.
- **P06 evidence / gap:** Acceptance/id tests pass. The latency target has not been
  benchmarked, and the in-memory store is not durable across process restarts.

## S4 · Explicit deposit failure

- **Source / stimulus:** The payment provider declines a deposit or times out.
- **Environment / artifact:** Future booking/payment integration with a 5-second
  provider timeout; Payments contract and payment records.
- **Response:** Return an explicit decline/failure and never record it as Paid.
  A timeout needs a defined failure mapping when a real provider is introduced.
- **Measure:** Across 100 injected declines/timeouts, zero false Paid outcomes;
  the caller receives a failure within 5 seconds in every case.
- **P06 evidence / gap:** The simulation returns Declined for zero/negative amounts
  and Paid for positive amounts. Booking does not invoke Payments; provider
  timeouts and payment persistence remain future work.

## S5 · Booking survives notification failure

- **Source / stimulus:** The confirmation sender raises a delivery exception.
- **Environment / artifact:** A valid booking has just been saved; BookingService
  and Notifications. The injected failure occurs immediately.
- **Response:** Keep Confirmed status and blocked nights; return Accepted with
  reservation id and `notification_failed=True`.
- **Measure:** Across 100 injected immediate failures, zero lost/cancelled bookings
  and 100 flagged Accepted results, each returned within 5 seconds.
- **P06 evidence / gap:** The original failed-confirmation test checks the Accepted
  result, flag and saved record. There is no queue, retry, logging or network
  timeout guarantee; a blocking real sender would need an explicit timeout.

## S6 · Rule changes stay in their owner

- **Source / stimulus:** A developer changes a Deluxe price, deposit percentage or
  delivery channel, or accidentally imports another module's implementation.
- **Environment / artifact:** Development/CI; the four module packages and their
  architecture checks.
- **Response:** Change only the owning module and its tests when the public
  contract is unchanged. Reject forbidden implementation imports.
- **Measure:** Zero source edits in the other three modules for such a rule change;
  all 8 behaviour tests and 3 architecture contracts pass. A forbidden import
  causes a nonzero lint exit naming its dependency.
- **P06 evidence / gap:** The SMS behaviour test passes without changing the booking
  rule; the deliberate internal import fails lint and is removed. Price/deposit
  policy edits cannot be demonstrated until those policies exist.

The measures above are acceptance targets, not unmeasured claims about the small
in-memory teaching app. See the P06 before/after evidence in `design-notes.md`.

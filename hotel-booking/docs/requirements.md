## R1 · Search
A guest or receptionist can list the rooms that are free for given dates.
Check: empty hotel, 12–14 November → R7, R8.

## R2 · Book
A guest or receptionist can book a free room. The app answers with a reservation id.
Check: Maya books R7 for 12–14 November → Accepted R101.

## R3 · No clash
A room never has two Confirmed bookings on the same night. Check-out must be after check-in.
Check: Omar asks for R7 on 13–15 → Unavailable. 15–15 → InvalidDates.

More examples:
Maya R7 12–14 → Confirmed (nights of the 12th and 13th).
Omar R7 13–15 → Unavailable (night of the 13th).
Nora R7 14–16 → Accepted (no shared night).
Alex R8 22–24 → Accepted (no shared night).
Sam R8 21–23 → Unavailable (night of the 21st).

## R4 · Cancel
A booking can be cancelled. It is kept as Cancelled and no longer blocks the room.
Check: Maya cancels R101 → R7 is free again for 12–14.

## R5 · View
A booking can be looked up by its id.
Check: R101 → Maya, R7, 12–14 November, Confirmed.

## R6 · Confirmation
Each accepted booking requests one confirmation for the guest. A refused booking
does not send a confirmation. Email and SMS senders implement the same contract.
If sending fails, the saved reservation remains Confirmed, the result remains
Accepted with its reservation id, and `notification_failed` is True.
Check: Maya and Nora book successfully, Omar is refused → two confirmations.
Check: the sender fails for Maya → Accepted R101, `notification_failed=True`,
and R101 is still saved and blocks the room.

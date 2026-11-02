# P07 API check

Start with `docker compose up --build`. Send these requests in order:

1. `curl.exe "http://localhost:5080/rooms?checkIn=2026-11-12&checkOut=2026-11-14"` → 200; R7 and R8.
2. `curl.exe -i -X POST http://localhost:5080/reservations -H "Content-Type: application/json" --data-binary @docs/requests/maya-r7.json` → 201; R101.
3. Repeat the POST with `docs/requests/omar-r7.json` → 409; Unavailable.
4. `curl.exe -i -X POST http://localhost:5080/reservations -H "Content-Type: application/json" --data-binary @docs/requests/omar-r8.json` → 400; InvalidDates.
5. `curl.exe -i -X DELETE http://localhost:5080/reservations/R101` → 204.
6. Repeat the DELETE → 404; NotFound.
7. Restart the app and search again; cancelled R101 remains stored, while R7 is available.

The API test suite also checks a successful room search, booking followed by conflict, invalid dates, and cancellation followed by not-found.

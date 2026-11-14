"""Send two overlapping bookings concurrently and print both API results.

Run the app with ``HOTEL_SLOW_STEP=1`` first:

    python tools/race_http.py
    python tools/race_http.py http://localhost:5081

The optional URL sends Omar to a second app instance while Maya still goes to
port 5080. Both instances must use the same PostgreSQL database.
"""
from __future__ import annotations

import json
import sys
import threading
import urllib.error
import urllib.request


MAYA = {
    "guestName": "Maya",
    "guestEmail": "maya@example.com",
    "roomNumber": "R7",
    "checkIn": "2026-11-12",
    "checkOut": "2026-11-14",
}
OMAR = {**MAYA, "guestName": "Omar", "guestEmail": "omar@example.com"}
REASONS = {201: "201 Created", 409: "409 Conflict", 400: "400 Bad Request"}


def book(base: str, body: dict[str, str]) -> str:
    request = urllib.request.Request(
        f"{base}/reservations",
        method="POST",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request) as response:
            return f"{REASONS.get(response.status, str(response.status))}   {response.read().decode()}"
    except urllib.error.HTTPError as error:
        return f"{REASONS.get(error.code, str(error.code))}  {error.read().decode()}"


def main() -> None:
    maya_base = "http://localhost:5080"
    omar_base = sys.argv[1] if len(sys.argv) > 1 else maya_base
    answers: dict[str, str] = {}

    with urllib.request.urlopen(f"{maya_base}/stats") as warm_up:
        warm_up.read()

    print("Two bookings for R7, 2026-11-12 to 2026-11-14, sent at the same moment.")
    if omar_base != maya_base:
        print(f"Maya -> {maya_base}   Omar -> {omar_base}")
    print()

    maya = threading.Thread(target=lambda: answers.update(Maya=book(maya_base, MAYA)))
    omar = threading.Thread(target=lambda: answers.update(Omar=book(omar_base, OMAR)))
    maya.start()
    threading.Event().wait(0.5)
    omar.start()
    maya.join()
    omar.join()

    print(f"Maya -> {answers['Maya']}")
    print(f"Omar -> {answers['Omar']}")
    print()
    accepted = sum(answer.startswith("201") for answer in answers.values())
    print(f"Accepted responses: {accepted}")
    print(
        "DOUBLE BOOKED: both requests were accepted."
        if accepted > 1
        else "CORRECT: one booking was accepted and one was refused."
    )


if __name__ == "__main__":
    main()

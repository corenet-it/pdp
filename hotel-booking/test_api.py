import threading
import unittest
from datetime import date

from fastapi.testclient import TestClient

from hotel_booking.api import ApiStats, create_app
from hotel_booking.api_cache import InMemoryAvailabilityCache
from hotel_booking.reservations import DateRange, Guest, OverlapRejected, Reservation
from hotel_booking.reservations.internal import InMemoryReservationStore
from hotel_booking.rooms import Room
from hotel_booking.rooms.internal import InMemoryRoomCatalog


R7 = Room("R7", "Standard")
MAYA = {"guestName": "Maya", "guestEmail": "maya@example.com", "roomNumber": "R7",
        "checkIn": "2026-11-12", "checkOut": "2026-11-14"}
OMAR = {**MAYA, "guestName": "Omar", "guestEmail": "omar@example.com"}


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.cache = InMemoryAvailabilityCache()
        self.stats = ApiStats()
        app = create_app(
            InMemoryRoomCatalog([R7, Room("R8", "Deluxe")]),
            InMemoryReservationStore(),
            self.cache,
            self.stats,
        )
        app.testing = True
        self.client = TestClient(app)

    def test_search_returns_rooms(self):
        response = self.client.get("/rooms?checkIn=2026-11-12&checkOut=2026-11-14")
        self.assertEqual(200, response.status_code)
        self.assertEqual(["R7", "R8"], [room["number"] for room in response.json()["rooms"]])
        self.client.get("/rooms?checkIn=2026-11-12&checkOut=2026-11-14")
        self.assertEqual(
            {"databaseQueries": 0, "cacheHits": 1, "cacheMisses": 1},
            self.client.get("/stats").json(),
        )

    def test_book_then_conflict(self):
        body = {"guestName": "Maya", "guestEmail": "maya@example.com", "roomNumber": "R7", "checkIn": "2026-11-12", "checkOut": "2026-11-14"}
        self.assertEqual(201, self.client.post("/reservations", json=body).status_code)
        body.update(checkIn="2026-11-13", checkOut="2026-11-15")
        self.assertEqual(409, self.client.post("/reservations", json=body).status_code)

    def test_wrong_dates_are_bad_request(self):
        body = {"guestName": "Maya", "guestEmail": "maya@example.com", "roomNumber": "R7", "checkIn": "2026-11-15", "checkOut": "2026-11-15"}
        self.assertEqual(400, self.client.post("/reservations", json=body).status_code)

    def test_cancel_then_not_found(self):
        body = {"guestName": "Maya", "guestEmail": "maya@example.com", "roomNumber": "R7", "checkIn": "2026-11-12", "checkOut": "2026-11-14"}
        reservation_id = self.client.post("/reservations", json=body).json()["reservationId"]
        self.assertEqual(204, self.client.delete(f"/reservations/{reservation_id}").status_code)
        self.assertEqual(404, self.client.delete(f"/reservations/{reservation_id}").status_code)

    def test_successful_booking_invalidates_cached_availability(self):
        url = "/rooms?checkIn=2026-11-12&checkOut=2026-11-14"
        self.client.get(url)
        body = {"guestName": "Maya", "guestEmail": "maya@example.com", "roomNumber": "R7", "checkIn": "2026-11-12", "checkOut": "2026-11-14"}

        self.assertEqual(201, self.client.post("/reservations", json=body).status_code)
        rooms = self.client.get(url).json()["rooms"]

        self.assertEqual(["R8"], [room["number"] for room in rooms])
        self.assertEqual(2, self.cache.version)

    def test_successful_cancellation_invalidates_cached_availability(self):
        body = {"guestName": "Maya", "guestEmail": "maya@example.com", "roomNumber": "R7", "checkIn": "2026-11-12", "checkOut": "2026-11-14"}
        reservation_id = self.client.post("/reservations", json=body).json()["reservationId"]
        url = "/rooms?checkIn=2026-11-12&checkOut=2026-11-14"
        self.client.get(url)

        self.assertEqual(204, self.client.delete(f"/reservations/{reservation_id}").status_code)
        rooms = self.client.get(url).json()["rooms"]

        self.assertEqual(["R7", "R8"], [room["number"] for room in rooms])
        self.assertEqual(3, self.cache.version)

    def test_two_bookings_at_the_same_moment_give_the_room_one_reservation(self):
        """Both pre-checks pass, but the store may save only one booking."""
        store = InMemoryReservationStore()
        app = create_app(
            InMemoryRoomCatalog([R7]), store, slow_step_seconds=0.3
        )
        client = TestClient(app)
        answers: dict[str, int] = {}

        maya = threading.Thread(
            target=lambda: answers.update(maya=client.post("/reservations", json=MAYA).status_code)
        )
        omar = threading.Thread(
            target=lambda: answers.update(omar=client.post("/reservations", json=OMAR).status_code)
        )
        maya.start()
        omar.start()
        maya.join()
        omar.join()

        self.assertEqual([201, 409], sorted(answers.values()))
        stay = DateRange(date(2026, 11, 12), date(2026, 11, 14))
        self.assertEqual(1, store.count_confirmed(R7, stay))

    def test_store_refuses_overlap_even_when_pre_check_is_bypassed(self):
        store = InMemoryReservationStore()
        stay = DateRange(date(2026, 11, 12), date(2026, 11, 14))
        store.save(Reservation("R101", Guest("Maya", "maya@example.com"), R7, stay))
        overlapping = Reservation(
            "R102",
            Guest("Omar", "omar@example.com"),
            R7,
            DateRange(date(2026, 11, 13), date(2026, 11, 15)),
        )

        with self.assertRaises(OverlapRejected):
            store.save(overlapping)
        self.assertEqual(1, store.count_confirmed(R7, stay))


if __name__ == "__main__":
    unittest.main()

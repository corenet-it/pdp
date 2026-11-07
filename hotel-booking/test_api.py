import unittest
from fastapi.testclient import TestClient

from hotel_booking.api import ApiStats, create_app
from hotel_booking.api_cache import InMemoryAvailabilityCache
from hotel_booking.reservations.internal import InMemoryReservationStore
from hotel_booking.rooms import Room
from hotel_booking.rooms.internal import InMemoryRoomCatalog


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.cache = InMemoryAvailabilityCache()
        self.stats = ApiStats()
        app = create_app(
            InMemoryRoomCatalog([Room("R7", "Standard"), Room("R8", "Deluxe")]),
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


if __name__ == "__main__":
    unittest.main()

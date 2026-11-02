import unittest
from fastapi.testclient import TestClient

from hotel_booking.api import create_app
from hotel_booking.reservations.internal import InMemoryReservationStore
from hotel_booking.rooms import Room
from hotel_booking.rooms.internal import InMemoryRoomCatalog


class ApiTests(unittest.TestCase):
    def setUp(self):
        app = create_app(InMemoryRoomCatalog([Room("R7", "Standard"), Room("R8", "Deluxe")]), InMemoryReservationStore())
        app.testing = True
        self.client = TestClient(app)

    def test_search_returns_rooms(self):
        response = self.client.get("/rooms?checkIn=2026-11-12&checkOut=2026-11-14")
        self.assertEqual(200, response.status_code)
        self.assertEqual(["R7", "R8"], [room["number"] for room in response.json["rooms"]])

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
        reservation_id = self.client.post("/reservations", json=body).json["reservationId"]
        self.assertEqual(204, self.client.delete(f"/reservations/{reservation_id}").status_code)
        self.assertEqual(404, self.client.delete(f"/reservations/{reservation_id}").status_code)


if __name__ == "__main__":
    unittest.main()

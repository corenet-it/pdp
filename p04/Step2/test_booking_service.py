"""Step 2: tests that describe what the P03 app does today.

They must pass before the refactoring and still pass after it.
"""
import unittest
from datetime import date

from hotel_booking import BookingService, DateRange, EmailSender, Guest, ReservationStore, Room

R7 = Room("R7", "Standard")
R8 = Room("R8", "Deluxe")
MAYA = Guest("Maya", "maya@example.com")
OMAR = Guest("Omar", "omar@example.com")
NORA = Guest("Nora", "nora@example.com")


def nov(check_in: int, check_out: int) -> DateRange:
    return DateRange(date(2026, 11, check_in), date(2026, 11, check_out))


def new_service():
    """The only place that builds the service: a refactoring changes this function, not every test."""
    store = ReservationStore()
    email = EmailSender()
    return BookingService([R7, R8], store, email), store, email


class BookingServiceTests(unittest.TestCase):
    def test_maya_gets_r7_when_it_is_free(self):
        service, _, _ = new_service()
        self.assertEqual("Accepted R101", str(service.reserve(MAYA, R7, nov(12, 14))))

    def test_omar_is_refused_when_a_night_is_shared(self):
        service, store, _ = new_service()
        service.reserve(MAYA, R7, nov(12, 14))
        self.assertEqual("Unavailable", str(service.reserve(OMAR, R7, nov(13, 15))))
        self.assertEqual(1, store.count())

    def test_nora_can_arrive_on_the_day_maya_leaves(self):
        service, _, _ = new_service()
        service.reserve(MAYA, R7, nov(12, 14))
        self.assertEqual("Accepted R102", str(service.reserve(NORA, R7, nov(14, 16))))

    def test_check_out_must_be_after_check_in(self):
        service, store, _ = new_service()
        self.assertEqual("InvalidDates", str(service.reserve(OMAR, R8, nov(15, 15))))
        self.assertEqual(0, store.count())

    def test_cancelling_frees_the_room_again(self):
        service, _, _ = new_service()
        service.reserve(MAYA, R7, nov(12, 14))
        self.assertTrue(service.cancel("R101"))
        self.assertIn(R7, service.find_free_rooms(nov(12, 14)))

    def test_one_confirmation_per_accepted_booking(self):
        service, _, email = new_service()
        service.reserve(MAYA, R7, nov(12, 14))
        service.reserve(OMAR, R7, nov(13, 15))
        service.reserve(NORA, R7, nov(14, 16))
        self.assertEqual(2, email.sent)


if __name__ == "__main__":
    unittest.main()

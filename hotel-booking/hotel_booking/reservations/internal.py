from __future__ import annotations

from hotel_booking.reservations.domain import DateRange, Reservation
from hotel_booking.rooms import Room
import os
from datetime import date
from typing import Callable
from hotel_booking.reservations.domain import Guest, ReservationStatus


class InMemoryReservationStore:
    """Keeps reservations in a list. P07 adds a PostgreSQL store with the same methods."""

    def __init__(self) -> None:
        self._rows: list[Reservation] = []

    def count(self) -> int:
        return len(self._rows)

    def has_overlap(self, room: Room, stay: DateRange) -> bool:
        return any(row.blocks(room, stay) for row in self._rows)

    def save(self, reservation: Reservation) -> None:
        self._rows.append(reservation)

    def find(self, reservation_id: str) -> Reservation | None:
        return next((row for row in self._rows if row.id == reservation_id), None)

    def count_confirmed(self, room: Room, stay: DateRange) -> int:
        return sum(1 for row in self._rows if row.blocks(room, stay))


class PostgresReservationStore:
    def __init__(self, dsn: str | None = None, on_query: Callable[[], None] | None = None) -> None:
        self.dsn = dsn or os.getenv("DATABASE_URL", "postgresql://hotel:hotel@localhost:5432/hotel")
        self.on_query = on_query or (lambda: None)

    def _connect(self):
        import psycopg
        return psycopg.connect(self.dsn)

    def count(self) -> int:
        with self._connect() as connection:
            self.on_query()
            return connection.execute("SELECT count(*) FROM reservations").fetchone()[0]

    def has_overlap(self, room: Room, stay: DateRange) -> bool:
        with self._connect() as connection:
            self.on_query()
            return connection.execute("SELECT EXISTS (SELECT 1 FROM reservations WHERE room_number=%s AND status='Confirmed' AND check_in < %s AND check_out > %s)", (room.number, stay.check_out, stay.check_in)).fetchone()[0]

    def save(self, reservation: Reservation) -> None:
        with self._connect() as connection:
            self.on_query()
            connection.execute("INSERT INTO reservations (id, guest_name, guest_email, room_number, check_in, check_out, status) VALUES (%s,%s,%s,%s,%s,%s,%s)", (reservation.id, reservation.guest.name, reservation.guest.email, reservation.room.number, reservation.stay.check_in, reservation.stay.check_out, reservation.status.value))

    def find(self, reservation_id: str) -> Reservation | None:
        with self._connect() as connection:
            self.on_query()
            row = connection.execute("SELECT id, guest_name, guest_email, room_number, check_in, check_out, status, type FROM reservations JOIN rooms ON rooms.number=reservations.room_number WHERE id=%s", (reservation_id,)).fetchone()
        if row is None:
            return None
        reservation = Reservation(row[0], Guest(row[1], row[2]), Room(row[3], row[7]), DateRange(row[4], row[5]))
        reservation.status = ReservationStatus(row[6])
        return reservation

    def count_confirmed(self, room: Room, stay: DateRange) -> int:
        with self._connect() as connection:
            self.on_query()
            return connection.execute("SELECT count(*) FROM reservations WHERE room_number=%s AND status='Confirmed' AND check_in < %s AND check_out > %s", (room.number, stay.check_out, stay.check_in)).fetchone()[0]

    def cancel(self, reservation_id: str) -> bool:
        with self._connect() as connection:
            self.on_query()
            cursor = connection.execute("UPDATE reservations SET status='Cancelled' WHERE id=%s AND status='Confirmed'", (reservation_id,))
            return cursor.rowcount > 0

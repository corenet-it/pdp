from __future__ import annotations

from hotel_booking.rooms.catalog import Room
import os
from typing import Callable


class PostgresRoomCatalog:
    def __init__(self, dsn: str | None = None, on_query: Callable[[], None] | None = None) -> None:
        self.dsn = dsn or os.getenv("DATABASE_URL", "postgresql://hotel:hotel@localhost:5432/hotel")
        self.on_query = on_query or (lambda: None)

    def all(self) -> list[Room]:
        import psycopg
        with psycopg.connect(self.dsn) as connection:
            self.on_query()
            rows = connection.execute("SELECT number, type FROM rooms ORDER BY number").fetchall()
        return [Room(number, room_type) for number, room_type in rows]


class InMemoryRoomCatalog:
    """Keeps the hotel's rooms in a list. Only main.py creates it."""

    def __init__(self, rooms: list[Room]) -> None:
        self._rooms = list(rooms)

    def all(self) -> list[Room]:
        return list(self._rooms)

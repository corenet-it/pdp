from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from datetime import date
from typing import Protocol

from hotel_booking.rooms import Room


@dataclass(frozen=True)
class CacheLookup:
    """A cache result plus the version under which it was read.

    Keeping the version with a miss prevents a concurrent invalidation from
    allowing an older database result to be written under the new version.
    """

    version: int | None
    rooms: list[Room] | None


class AvailabilityCache(Protocol):
    def get(self, check_in: date, check_out: date) -> CacheLookup: ...

    def put(self, check_in: date, check_out: date, version: int | None,
            rooms: list[Room]) -> None: ...

    def invalidate(self) -> None: ...


class RedisAvailabilityCache:
    VERSION_KEY = "availability:version"

    def __init__(self, client, ttl_seconds: int = 30) -> None:
        self.client = client
        self.ttl_seconds = ttl_seconds

    @classmethod
    def from_url(cls, url: str, ttl_seconds: int = 30) -> "RedisAvailabilityCache":
        from redis import Redis

        return cls(Redis.from_url(url, decode_responses=True), ttl_seconds)

    @staticmethod
    def _key(version: int, check_in: date, check_out: date) -> str:
        return f"availability:v{version}:{check_in.isoformat()}:{check_out.isoformat()}"

    def _version(self) -> int:
        self.client.set(self.VERSION_KEY, 1, nx=True)
        return int(self.client.get(self.VERSION_KEY))

    def get(self, check_in: date, check_out: date) -> CacheLookup:
        try:
            version = self._version()
            payload = self.client.get(self._key(version, check_in, check_out))
            if payload is None:
                return CacheLookup(version, None)
            rows = json.loads(payload)
            return CacheLookup(version, [Room(row["number"], row["type"]) for row in rows])
        except Exception:
            # Redis is an optimisation. Search still works from PostgreSQL when
            # the cache is unavailable or contains an invalid value.
            return CacheLookup(None, None)

    def put(self, check_in: date, check_out: date, version: int | None,
            rooms: list[Room]) -> None:
        if version is None:
            return
        payload = json.dumps([{"number": room.number, "type": room.type} for room in rooms])
        try:
            self.client.setex(self._key(version, check_in, check_out), self.ttl_seconds, payload)
        except Exception:
            pass

    def invalidate(self) -> None:
        try:
            self.client.set(self.VERSION_KEY, 1, nx=True)
            self.client.incr(self.VERSION_KEY)
        except Exception:
            # Correctness does not depend on Redis: writes always use PostgreSQL
            # and cached values expire after the short TTL.
            pass


class InMemoryAvailabilityCache:
    """Small test adapter with the same versioned behaviour as Redis."""

    def __init__(self) -> None:
        self.version = 1
        self._values: dict[str, list[Room]] = {}
        self._lock = threading.Lock()

    @staticmethod
    def _key(version: int, check_in: date, check_out: date) -> str:
        return f"availability:v{version}:{check_in.isoformat()}:{check_out.isoformat()}"

    def get(self, check_in: date, check_out: date) -> CacheLookup:
        with self._lock:
            rooms = self._values.get(self._key(self.version, check_in, check_out))
            return CacheLookup(self.version, None if rooms is None else list(rooms))

    def put(self, check_in: date, check_out: date, version: int | None,
            rooms: list[Room]) -> None:
        if version is None:
            return
        with self._lock:
            self._values[self._key(version, check_in, check_out)] = list(rooms)

    def invalidate(self) -> None:
        with self._lock:
            self.version += 1

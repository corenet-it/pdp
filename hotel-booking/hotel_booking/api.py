from __future__ import annotations

from datetime import date
from pathlib import Path
import threading

from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse, Response

from hotel_booking.api_cache import AvailabilityCache
from hotel_booking.notifications.internal import EmailNotificationSender
from hotel_booking.reservations import BookingService, DateRange, Guest


class ApiStats:
    def __init__(self) -> None:
        self._database_queries = 0
        self._cache_hits = 0
        self._cache_misses = 0
        self._lock = threading.Lock()

    def database_query(self) -> None:
        with self._lock:
            self._database_queries += 1

    def cache_hit(self) -> None:
        with self._lock:
            self._cache_hits += 1

    def cache_miss(self) -> None:
        with self._lock:
            self._cache_misses += 1

    def snapshot(self) -> dict[str, int]:
        with self._lock:
            return {
                "databaseQueries": self._database_queries,
                "cacheHits": self._cache_hits,
                "cacheMisses": self._cache_misses,
            }


def create_app(catalog, store, cache: AvailabilityCache | None = None,
               stats: ApiStats | None = None) -> FastAPI:
    app = FastAPI(title="Hotel Booking API", version="1.0.0", openapi_url="/openapi.json", docs_url="/docs")
    app_stats = stats or ApiStats()
    rooms = catalog.all()

    def service() -> BookingService:
        return BookingService(rooms, store, EmailNotificationSender())

    @app.get("/openapi.yaml", include_in_schema=False)
    def openapi_yaml():
        return Response((Path(__file__).parent.parent / "docs/openapi.yaml").read_text(), media_type="text/yaml")

    @app.get("/stats")
    def get_stats():
        return app_stats.snapshot()

    @app.get("/rooms")
    def search(checkIn: date, checkOut: date, limit: int = Query(20, ge=1, le=100), after: str = ""):
        stay = DateRange(checkIn, checkOut)
        if not stay.is_valid():
            return JSONResponse({"error": "checkOut must be after checkIn"}, status_code=400)
        lookup = cache.get(checkIn, checkOut) if cache is not None else None
        if lookup is not None and lookup.rooms is not None:
            app_stats.cache_hit()
            available = lookup.rooms
        else:
            if cache is not None:
                app_stats.cache_miss()
            available = service().find_free_rooms(stay)
            if cache is not None:
                cache.put(checkIn, checkOut, lookup.version if lookup is not None else None, available)
        return {"rooms": [{"number": room.number, "type": room.type} for room in available if room.number > after][:limit]}

    @app.post("/reservations", status_code=201)
    async def book(request: Request):
        body = await request.json()
        try:
            stay = DateRange(date.fromisoformat(body["checkIn"]), date.fromisoformat(body["checkOut"]))
            guest = Guest(body["guestName"], body["guestEmail"])
            room = next(room for room in rooms if room.number == body["roomNumber"])
        except (KeyError, TypeError, ValueError, StopIteration):
            return JSONResponse({"error": "Invalid booking request"}, status_code=400)
        result = service().reserve(guest, room, stay)
        if result.outcome == "InvalidDates":
            return JSONResponse({"error": result.outcome}, status_code=400)
        if result.outcome == "Unavailable":
            return JSONResponse({"error": result.outcome}, status_code=409)
        if cache is not None:
            cache.invalidate()
        return {"reservationId": result.reservation_id, "status": "Confirmed"}

    @app.delete("/reservations/{reservation_id}", status_code=204)
    def cancel(reservation_id: str):
        if not service().cancel(reservation_id):
            return JSONResponse({"error": "NotFound"}, status_code=404)
        if cache is not None:
            cache.invalidate()
        return Response(status_code=204)

    return app

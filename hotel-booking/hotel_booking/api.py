from __future__ import annotations

from datetime import date
from pathlib import Path

from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse, Response

from hotel_booking.notifications.internal import EmailNotificationSender
from hotel_booking.reservations import BookingService, DateRange, Guest


def create_app(catalog, store) -> FastAPI:
    app = FastAPI(title="Hotel Booking API", version="1.0.0", openapi_url="/openapi.json", docs_url="/docs")

    def service() -> BookingService:
        return BookingService(catalog.all(), store, EmailNotificationSender())

    @app.get("/openapi.yaml", include_in_schema=False)
    def openapi_yaml():
        return Response((Path(__file__).parent.parent / "docs/openapi.yaml").read_text(), media_type="text/yaml")

    @app.get("/rooms")
    def search(checkIn: date, checkOut: date, limit: int = Query(20, ge=1, le=100), after: str = ""):
        stay = DateRange(checkIn, checkOut)
        if not stay.is_valid():
            return JSONResponse({"error": "checkOut must be after checkIn"}, status_code=400)
        available = service().find_free_rooms(stay)
        return {"rooms": [{"number": room.number, "type": room.type} for room in available if room.number > after][:limit]}

    @app.post("/reservations", status_code=201)
    async def book(request: Request):
        body = await request.json()
        try:
            stay = DateRange(date.fromisoformat(body["checkIn"]), date.fromisoformat(body["checkOut"]))
            guest = Guest(body["guestName"], body["guestEmail"])
            room = next(room for room in catalog.all() if room.number == body["roomNumber"])
        except (KeyError, TypeError, ValueError, StopIteration):
            return JSONResponse({"error": "Invalid booking request"}, status_code=400)
        result = service().reserve(guest, room, stay)
        if result.outcome == "InvalidDates":
            return JSONResponse({"error": result.outcome}, status_code=400)
        if result.outcome == "Unavailable":
            return JSONResponse({"error": result.outcome}, status_code=409)
        return {"reservationId": result.reservation_id, "status": "Confirmed"}

    @app.delete("/reservations/{reservation_id}", status_code=204)
    def cancel(reservation_id: str):
        if not service().cancel(reservation_id):
            return JSONResponse({"error": "NotFound"}, status_code=404)
        return Response(status_code=204)

    return app

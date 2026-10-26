## Why design before code

Low-level design decides which classes the system needs, what data each class stores, which methods it provides, and how the classes call each other.

## 2.1 User
- Data: id, name, email, age, role
- Methods: create(), update()

## 2.2 Room
- Data: id, name, price, status
- Methods: getDetails(), checkAvailability()

## 2.3 Booking
- Data: id, userId, roomId, startDate, endDate, status
- Methods: create(), cancel()

## 2.4 BookingService
- Methods: createBooking(), cancelBooking()
- Interactions: checks room availability and creates or cancels bookings.

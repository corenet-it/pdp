P07 · The app gets an address and a database
In L04 you estimated the load and followed a request to the database. Today the P06 app becomes a web app on http://localhost:5080, and its reservations move into PostgreSQL.

Activity sheet (opens in a new tab)
Printable presentation (opens in a new tab)
Where we are
?
Your hotel-booking folder has the P06 code: four modules, 8 behaviour tests and 3 border checks, a demo and a race. docs/l04-notes.md has your three answers from L04.

Why that is not enough now
What the hotel needs	What the P06 app does
200 guests search within one minute (S1)	Only the person at the laptop can use it: there is no address to send a search to.
Maya’s booking is still there tomorrow	The reservations are a list in memory: stopping the program deletes them.
Two copies of the app agree about R7 (L04)	Each copy has its own list, so both can accept R7.
Today’s plan
Step	What you do	Where it goes
1 · Capacity estimate	Write today’s assumptions and calculations for your app: requests, storage, bandwidth, and what to measure later	docs/capacity.md
2 · Start PostgreSQL	Add docker-compose.yml and db/init.sql; docker compose up -d; check that rooms R7 and R8 are there	docker-compose.yml, db/init.sql
3 · The API contract	Describe the three operations, their answers and their errors	docs/openapi.yaml
4 · From console to web app	Install your framework; the app listens on http://localhost:5080 and serves /openapi.yaml; --demo and --race still print the P06 lines	your project file and the wiring
5 · The three endpoints	Turn every booking answer into an HTTP status and body; limit and after for the search; still the in-memory store; check them with curl.exe	the Api folder, outside the four modules; docs/requests/
6 · API tests	Four tests through your framework’s test client: search 200, book 201 then 409, wrong dates 400, cancel 204 then 404	the API test file
7 · PostgreSQL stores	A reservation store and a room catalog that read and write the init.sql tables; the booking rule does not change (JavaScript and Dart: BookingService awaits the store)	the Rooms and Reservations internal code
8 · Plug it in and prove it	The wiring picks the PostgreSQL stores; run the seven requests; restart the app and Maya’s booking is still there	the wiring, docs/api-check.md
How you work today
Work in pairs on one laptop, in the hotel-booking folder from P06, in the same language as before. Swap who types at every new step. Every code slide has a tab for each of the six languages.

You need Docker Desktop running (PostgreSQL 18 runs inside it), your editor, a terminal opened in the hotel-booking folder and your browser. curl.exe is built into Windows 10 and 11. Internet is needed once, in Steps 2 and 4, to download PostgreSQL and your language’s packages.

If you missed P06: download the P06 runnable code in your language from the P06 lesson page. The “Runnable code” link on this page has the finished P07 project in all six languages.

Completed example: your folder at the end of P07
hotel-booking folder
Copy output
C#
Python
Java
Go
JavaScript
Dart
hotel-booking/   end of P07
├── db/
│   └── init.sql   NEW: the rooms and reservations tables
├── docs/
│   ├── requests/   NEW: the request bodies curl sends
│   │   ├── maya-r7.json
│   │   ├── omar-r7.json
│   │   └── omar-r8.json
│   ├── adr-001-modular-monolith.md
│   ├── api-check.md   NEW: seven requests and their answers
│   ├── capacity.md   NEW: the estimate
│   ├── contexts.md
│   ├── design-notes.md
│   ├── diagrams.drawio
│   ├── l04-notes.md
│   ├── openapi.yaml   NEW: the API contract
│   ├── quality-scenarios.md
│   └── requirements.md
├── hotel_booking/
│   ├── notifications/
│   │   ├── __init__.py
│   │   └── internal.py
│   ├── payments/
│   │   ├── __init__.py
│   │   └── internal.py
│   ├── reservations/
│   │   ├── __init__.py
│   │   ├── booking.py
│   │   ├── domain.py
│   │   └── internal.py   CHANGED: + PostgresReservationStore
│   ├── rooms/
│   │   ├── __init__.py
│   │   ├── catalog.py
│   │   └── internal.py   CHANGED: + PostgresRoomCatalog
│   ├── __init__.py
│   └── api.py   NEW
├── docker-compose.yml   NEW: PostgreSQL in Docker
├── main.py   CHANGED: web app; the wiring picks the PostgreSQL stores
├── pyproject.toml
├── requirements.txt   NEW
├── test_api.py   NEW
└── test_booking_service.py
Your turn · open your project
Start Docker Desktop and wait until it says “Engine running”.
Open your hotel-booking folder in your editor, and open a terminal in the same folder.
Run your P06 checks once: 11 green (Python: 8 tests, then “Contracts: 3 kept”).
Open docs/design-notes.md and add a new heading at the bottom: # P07 design notes
Open docs/l04-notes.md: its first line, the peak, is where Step 1 starts.
When you finish, you have: Docker Desktop running, your P06 project open with green checks, and a “P07 design notes” heading.
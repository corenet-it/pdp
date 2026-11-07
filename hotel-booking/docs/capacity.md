# P07 capacity estimate

## Assumptions

- S1: 200 guests search in one minute; assumed one search per guest, or 3.33 requests/second average. Plan for a 3x burst: 10 requests/second.
- A search request/response is estimated at 1.5 KB total: about 300 KB/minute at the stated load (0.5 KB/second average).
- Each reservation row, including indexes and PostgreSQL overhead, is budgeted at 1 KB. At 100 new reservations/day: about 36.5 MB/year; room rows are negligible.
- A 10-request/second search workload at 1.5 KB/request is about 15 KB/second of application traffic.

## P08 measurement

`tools/measure.py` now records the average and p95 HTTP latency for 1,000
searches. `GET /stats` records executed PostgreSQL statements, cache hits and
cache misses. The measurement tool takes before/after snapshots, so the
one-time room-catalog query at application startup is not included.

With the current two-room seed, an uncached search executes two overlap
queries: 1,000 searches therefore execute 2,000 database queries. After an
empty-cache first request, the cache-aside run executes two database queries,
then serves 999 hits from Redis. On the delivery laptop the uncached run was
9.42 ms average / 14.26 ms p95; cache-aside was 2.17 ms average / 4.35 ms p95.
The reproducible commands and measurement scope are in
`docs/cache-experiment.md`.

Still to measure before selecting production capacity: realistic room and
reservation counts, concurrent request rate, p50/p99 latency, response bytes,
PostgreSQL query latency and connection use, rows per day, and error rate.

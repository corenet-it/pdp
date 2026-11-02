# P07 capacity estimate

## Assumptions

- S1: 200 guests search in one minute; assumed one search per guest, or 3.33 requests/second average. Plan for a 3x burst: 10 requests/second.
- A search request/response is estimated at 1.5 KB total: about 300 KB/minute at the stated load (0.5 KB/second average).
- Each reservation row, including indexes and PostgreSQL overhead, is budgeted at 1 KB. At 100 new reservations/day: about 36.5 MB/year; room rows are negligible.
- A 10-request/second search workload at 1.5 KB/request is about 15 KB/second of application traffic.

## Measure next

Record request rate and p50/p95/p99 latency by endpoint, response bytes, PostgreSQL query latency and connection use, rows per day, and error rate. Load-test the burst against realistic room/reservation counts before selecting production capacity. These are planning estimates, not benchmark results.

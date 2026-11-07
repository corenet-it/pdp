# P08 cache experiment

## Method

Both runs use 1,000 sequential requests for 12–14 November 2026 against the
same two-room database. The tool reads `/stats` immediately before and after
the run and reports the counter difference.

```sh
# No cache: recreate the app with caching disabled, then run:
CACHE_ENABLED=false docker compose up -d --force-recreate app
python tools/measure.py

# Cache-aside: recreate the app with caching enabled, empty Redis, then run:
CACHE_ENABLED=true docker compose up -d --force-recreate app
docker compose exec cache redis-cli FLUSHDB
python tools/measure.py
```

| Variant | Average | p95 | Database queries | Cache hits / misses |
|---|---:|---:|---:|---:|
| No cache | 9.42 ms | 14.26 ms | 2,000 | 0 / 0 |
| Cache-aside, TTL 30 s | 2.17 ms | 4.35 ms | 2 | 999 / 1 |

Measured on 7 November 2026 on the delivery laptop with Docker Desktop 29.9.2,
using the commands above. These are local development measurements, not a
production capacity guarantee.

The database-query reduction is 99.9% for this repeated-key workload. It is a
useful indicator for S6, but it is not itself an energy measurement. Energy per
1,000 searches still needs host/container power telemetry to verify the 20%
target.

## Stale result

Before mutation invalidation was connected, the controlled sequence was:

1. Search 12–14 Nov and cache `R7, R8`.
2. Maya books R7 successfully in PostgreSQL.
3. Search the same dates again and receive the stale cached `R7, R8`.
4. Omar asks to book R7 and receives `409 Unavailable`, because booking checks
   PostgreSQL rather than Redis.

The final implementation invalidates after every successful POST and DELETE,
so step 3 misses under the new version and returns only R8. API tests cover both
mutation paths.

## Hot key and next bottleneck

If every guest searches 31 Dec–2 Jan, they share one Redis key. Search database
work nearly disappears after the first request. The pressure moves to
`POST /reservations` and PostgreSQL: overlap checking, reservation counting and
inserting still execute for every attempt. P09 should make that write path
atomic; cache work must not disguise the existing check-then-save race.

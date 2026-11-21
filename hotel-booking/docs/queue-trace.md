# P10 · Confirmation queue trace

Measured inside the Docker app container over loopback HTTP, using PostgreSQL,
Redis and a one-second simulated send. Each mode started in a fresh API process.
Requests booked adjacent, non-overlapping nights in R7. The snapshot was taken
immediately after the last POST. All test reservations were then cancelled.

| Mode | HTTP 201 | Median POST | Waiting | Sent | Failed | Dropped |
|---|---:|---:|---:|---:|---:|---:|
| Synchronous | 1/1 | 1052 ms | 0 | 1 | 0 | 0 |
| Unbounded FIFO | 30/30 | 25.3 ms | 29 | 0 | 0 | 0 |
| FIFO, capacity 8 | 30/30 | 26.6 ms | 8 | 0 | 0 | 21 |

One send was in progress in both queued runs. On GET /stats, queued is the
current waiting depth. Sent, failed and dropped are cumulative per process.
Only a committed booking submits an email. Saturation discards the newest
email while preserving the booking.

After cancellation of the test bookings, graceful shutdown took 29.1 seconds
for the unbounded worker and 7.9 seconds for the bounded worker as they finished
accepted mail. Cancellation does not retract an already submitted confirmation.
In a separate forced-stop probe, one simulated delivery was sleeping and two
were waiting when the worker process received SIGKILL. No delivery completed.
Pending messages have no persistent copy to replay after restart.

## Repeat with Docker

Run these commands from the project root. Each burst creates real reservations,
so select unused starting dates. Allow the queue to drain before changing modes
if you want all accepted deliveries to finish.

```sh
NOTIFICATION_CAPACITY=sync docker compose up -d --build --wait
python tools/burst.py 2098-02-01 --count 1
NOTIFICATION_CAPACITY=0 docker compose up -d --wait
python tools/burst.py 2098-03-01
NOTIFICATION_CAPACITY=8 docker compose up -d --wait
python tools/burst.py 2098-05-01
curl http://localhost:5080/stats
```

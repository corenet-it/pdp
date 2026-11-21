"""Book distinct one-night stays. Pick an unused start date for each run."""
import argparse
import json
from collections import Counter
from datetime import date, timedelta
from statistics import median
from time import perf_counter
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("start", type=date.fromisoformat)
    parser.add_argument("--count", type=int, default=30)
    parser.add_argument("--url", default="http://localhost:5080")
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be positive")
    statuses = Counter()
    timings = []
    for offset in range(args.count):
        day = args.start + timedelta(days=offset)
        body = {"guestName": "Burst", "guestEmail": "burst@example.com", "roomNumber": "R7",
                "checkIn": day.isoformat(), "checkOut": (day + timedelta(days=1)).isoformat()}
        request = Request(args.url + "/reservations", data=json.dumps(body).encode(),
                          headers={"Content-Type": "application/json"})
        start = perf_counter()
        try:
            with urlopen(request, timeout=30) as response:
                statuses[response.status] += 1
        except HTTPError as error:
            statuses[error.code] += 1
        timings.append((perf_counter() - start) * 1000)
    with urlopen(args.url + "/stats", timeout=10) as response:
        print(dict(statuses), f"median {median(timings):.1f} ms", json.load(response))
    if statuses[201] != args.count:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

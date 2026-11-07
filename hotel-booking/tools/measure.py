#!/usr/bin/env python3
"""Measure 1,000 availability searches and report the /stats delta."""

from __future__ import annotations

import argparse
import json
import math
import time
from urllib.parse import urlencode
from urllib.request import urlopen


def get_json(url: str) -> dict:
    with urlopen(url, timeout=10) as response:
        return json.load(response)


def percentile(values: list[float], percentage: float) -> float:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(len(ordered) * percentage) - 1)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:5080")
    parser.add_argument("--requests", type=int, default=1000)
    parser.add_argument("--check-in", default="2026-11-12")
    parser.add_argument("--check-out", default="2026-11-14")
    args = parser.parse_args()

    if args.requests < 1:
        parser.error("--requests must be at least 1")

    base_url = args.base_url.rstrip("/")
    search_url = f"{base_url}/rooms?{urlencode({'checkIn': args.check_in, 'checkOut': args.check_out})}"
    before = get_json(f"{base_url}/stats")
    latencies: list[float] = []

    for _ in range(args.requests):
        started = time.perf_counter()
        get_json(search_url)
        latencies.append((time.perf_counter() - started) * 1000)

    after = get_json(f"{base_url}/stats")
    delta = {name: after[name] - before[name] for name in after}
    print(json.dumps({
        "requests": args.requests,
        "averageMs": round(sum(latencies) / len(latencies), 2),
        "p95Ms": round(percentile(latencies, 0.95), 2),
        "statsDelta": delta,
    }, indent=2))


if __name__ == "__main__":
    main()

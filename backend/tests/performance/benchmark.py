"""Lightweight concurrency benchmark against a real running instance - no locust web UI, just fast
pass/fail-style numbers (p50/p95/p99 latency, throughput, error rate) suitable for a CI gate or a quick
"did this change regress latency" check. Complements locustfile.py rather than replacing it: this is for a
single endpoint's numbers on demand; locust is for shaped, sustained, multi-endpoint traffic.

Usage:
    python tests/performance/benchmark.py --host http://localhost:8000 --path "/api/v1/products?limit=20" \\
        --concurrency 20 --requests 200
"""
import argparse
import asyncio
import statistics
import time

import httpx


async def _one_request(client: httpx.AsyncClient, path: str) -> tuple[float, int]:
    started = time.perf_counter()
    try:
        response = await client.get(path)
        return (time.perf_counter() - started, response.status_code)
    except Exception:
        return (time.perf_counter() - started, 0)


async def run(host: str, path: str, concurrency: int, total_requests: int) -> None:
    async with httpx.AsyncClient(base_url=host, timeout=30.0) as client:
        durations: list[float] = []
        statuses: list[int] = []
        semaphore = asyncio.Semaphore(concurrency)

        async def _bounded() -> None:
            async with semaphore:
                duration, status = await _one_request(client, path)
                durations.append(duration)
                statuses.append(status)

        overall_start = time.perf_counter()
        await asyncio.gather(*(_bounded() for _ in range(total_requests)))
        overall_duration = time.perf_counter() - overall_start

    durations.sort()
    success = sum(1 for s in statuses if 200 <= s < 400)
    status_counts: dict[int, int] = {}
    for status in statuses:
        status_counts[status] = status_counts.get(status, 0) + 1
    p50 = durations[len(durations) // 2]
    p95 = durations[int(len(durations) * 0.95) - 1]
    p99 = durations[int(len(durations) * 0.99) - 1]

    print(f"Target:        {host}{path}")
    print(f"Requests:      {total_requests} at concurrency {concurrency}")
    print(f"Success rate:  {success}/{total_requests} ({success / total_requests * 100:.1f}%)")
    # Status breakdown matters more than a bare success rate: a wall of 429s means the rate limiter is doing
    # its job under this load, not that the endpoint is broken - a 500 means the endpoint is actually broken.
    print(f"Status codes:  {dict(sorted(status_counts.items()))}")
    print(f"Throughput:    {total_requests / overall_duration:.1f} req/s")
    print(f"Latency p50:   {p50 * 1000:.1f} ms")
    print(f"Latency p95:   {p95 * 1000:.1f} ms")
    print(f"Latency p99:   {p99 * 1000:.1f} ms")
    print(f"Latency max:   {max(durations) * 1000:.1f} ms")
    print(f"Latency mean:  {statistics.mean(durations) * 1000:.1f} ms")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="http://localhost:8000")
    parser.add_argument("--path", default="/health")
    parser.add_argument("--concurrency", type=int, default=10)
    parser.add_argument("--requests", type=int, default=100)
    args = parser.parse_args()
    asyncio.run(run(args.host, args.path, args.concurrency, args.requests))

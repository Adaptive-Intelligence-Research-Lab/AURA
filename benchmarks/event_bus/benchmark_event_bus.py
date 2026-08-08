"""Event Bus Performance Benchmark — AURA-IMPL-001 S37-38."""
from __future__ import annotations

import asyncio
import statistics
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from aura.execution.providers import EchoProvider
from aura.models.actions import Action
from aura.models.events import Event, EventType
from aura.runtime.event_bus.bus import EventBus
from aura.runtime.kernel import AURARuntime


async def bench_event_throughput(count: int) -> dict:
    bus = EventBus()
    await bus.start()
    async def noop(event: Event) -> None:
        pass
    bus.subscribe(EventType.ACTION_CREATED, noop)
    start = time.perf_counter()
    for i in range(count):
        await bus.publish(Event(event_type=EventType.ACTION_CREATED, source="bench", payload={"i": i}))
    elapsed = time.perf_counter() - start
    await bus.stop()
    return {"events": count, "elapsed_s": round(elapsed, 4), "throughput_eps": round(count / elapsed, 0)}


async def bench_event_latency(count: int) -> dict:
    bus = EventBus()
    await bus.start()
    latencies = []
    send_times: dict[str, float] = {}
    async def measure(event: Event) -> None:
        recv_time = time.perf_counter()
        eid = str(event.event_id)
        if eid in send_times:
            latencies.append((recv_time - send_times.pop(eid)) * 1_000_000)
    bus.subscribe(EventType.ACTION_CREATED, measure)
    for _ in range(count):
        send_time = time.perf_counter()
        event = Event(event_type=EventType.ACTION_CREATED, source="bench", payload={})
        send_times[str(event.event_id)] = send_time
        await bus.publish(event)
    await bus.stop()
    if not latencies:
        return {"count": 0}
    latencies.sort()
    return {
        "count": len(latencies),
        "p50_us": round(statistics.median(latencies), 1),
        "p95_us": round(latencies[int(len(latencies) * 0.95)], 1),
        "p99_us": round(latencies[int(len(latencies) * 0.99)], 1),
    }


async def bench_subscriber_scaling(num_subscribers: int, num_events: int) -> dict:
    bus = EventBus()
    await bus.start()
    received = [0] * num_subscribers
    def make_handler(idx: int):
        async def handler(event: Event) -> None:
            received[idx] += 1
        return handler
    for i in range(num_subscribers):
        bus.subscribe(EventType.ACTION_CREATED, make_handler(i))
    start = time.perf_counter()
    for _ in range(num_events):
        await bus.publish(Event(event_type=EventType.ACTION_CREATED, source="bench", payload={}))
    elapsed = time.perf_counter() - start
    await bus.stop()
    return {
        "subscribers": num_subscribers, "events": num_events,
        "elapsed_s": round(elapsed, 4), "throughput_eps": round(num_events / elapsed, 0),
        "all_received": all(r == num_events for r in received),
    }


async def bench_kernel_lifecycle() -> dict:
    startup_times = []
    shutdown_times = []
    for _ in range(10):
        runtime = AURARuntime()
        start = time.perf_counter()
        await runtime.initialize()
        await runtime.start()
        startup_times.append((time.perf_counter() - start) * 1000)
        start = time.perf_counter()
        await runtime.stop()
        shutdown_times.append((time.perf_counter() - start) * 1000)
    return {
        "iterations": 10,
        "startup_ms": {"p50": round(statistics.median(startup_times), 2), "min": round(min(startup_times), 2), "max": round(max(startup_times), 2)},
        "shutdown_ms": {"p50": round(statistics.median(shutdown_times), 2), "min": round(min(shutdown_times), 2), "max": round(max(shutdown_times), 2)},
    }


async def bench_action_execution(count: int) -> dict:
    runtime = AURARuntime()
    await runtime.initialize()
    await runtime.start()
    await runtime.register_capability(EchoProvider())
    latencies = []
    for _ in range(count):
        action = Action(capability_id="core.echo", parameters={"message": "bench"})
        start = time.perf_counter()
        await runtime.execute(action)
        latencies.append((time.perf_counter() - start) * 1000)
    await runtime.stop()
    latencies.sort()
    return {
        "actions": count,
        "latency_ms": {
            "p50": round(statistics.median(latencies), 2),
            "p95": round(latencies[int(len(latencies) * 0.95)], 2),
            "p99": round(latencies[int(len(latencies) * 0.99)], 2),
            "min": round(min(latencies), 2), "max": round(max(latencies), 2),
        },
    }


async def run_all() -> dict:
    results = {}
    print("Benchmarking event throughput...")
    for n in [1000, 10000, 100000]:
        results[f"throughput_{n}"] = await bench_event_throughput(n)
        print(f"  {n} events: {results[f'throughput_{n}']['throughput_eps']} eps")
    print("Benchmarking event latency...")
    results["latency"] = await bench_event_latency(10000)
    print(f"  p50={results['latency'].get('p50_us', 0)}us p99={results['latency'].get('p99_us', 0)}us")
    print("Benchmarking subscriber scaling...")
    for n in [1, 10, 100]:
        results[f"subscribers_{n}"] = await bench_subscriber_scaling(n, 1000)
        print(f"  {n} subscribers: {results[f'subscribers_{n}']['throughput_eps']} eps")
    print("Benchmarking kernel lifecycle...")
    results["lifecycle"] = await bench_kernel_lifecycle()
    print(f"  startup p50={results['lifecycle']['startup_ms']['p50']}ms")
    print("Benchmarking action execution...")
    results["execution"] = await bench_action_execution(1000)
    print(f"  p50={results['execution']['latency_ms']['p50']}ms p99={results['execution']['latency_ms']['p99']}ms")
    return results


def main() -> None:
    print("=" * 60)
    print("AURA v0.1 Event Bus Performance Benchmark")
    print("=" * 60)
    results = asyncio.run(run_all())
    print()
    print("Full results:")
    for k, v in results.items():
        print(f"  {k}: {v}")
    print("=" * 60)


if __name__ == "__main__":
    main()

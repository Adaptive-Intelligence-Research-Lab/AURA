"""In-memory metrics collection for AURA runtime (§33)."""
from __future__ import annotations

import threading
from typing import Any


class MetricsCollector:
    """Thread-safe in-memory metrics counter."""

    def __init__(self) -> None:
        self._counters: dict[str, int] = {}
        self._timers: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def increment(self, name: str, value: int = 1) -> None:
        with self._lock:
            self._counters[name] = self._counters.get(name, 0) + value

    def record_duration(self, name: str, duration_ms: float) -> None:
        with self._lock:
            if name not in self._timers:
                self._timers[name] = []
            self._timers[name].append(duration_ms)

    def get_counter(self, name: str) -> int:
        with self._lock:
            return self._counters.get(name, 0)

    def get_timer_stats(self, name: str) -> dict[str, float]:
        with self._lock:
            values = self._timers.get(name, [])
        if not values:
            return {"count": 0, "min": 0, "max": 0, "avg": 0}
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
        }

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "counters": dict(self._counters),
                "timers": {
                    k: {
                        "count": len(v),
                        "min": min(v) if v else 0,
                        "max": max(v) if v else 0,
                        "avg": sum(v) / len(v) if v else 0,
                    }
                    for k, v in self._timers.items()
                },
            }

    def reset(self) -> None:
        with self._lock:
            self._counters.clear()
            self._timers.clear()

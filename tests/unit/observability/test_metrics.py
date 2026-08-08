"""Tests for MetricsCollector — §33."""
import threading

from aura.observability.metrics import MetricsCollector


class TestMetricsCollector:
    def test_increment(self):
        mc = MetricsCollector()
        mc.increment("actions_total")
        mc.increment("actions_total")
        mc.increment("actions_total", 5)
        assert mc.get_counter("actions_total") == 7

    def test_increment_default_value(self):
        mc = MetricsCollector()
        mc.increment("test")
        assert mc.get_counter("test") == 1

    def test_get_counter_nonexistent(self):
        mc = MetricsCollector()
        assert mc.get_counter("nonexistent") == 0

    def test_record_duration(self):
        mc = MetricsCollector()
        mc.record_duration("execution", 10.5)
        mc.record_duration("execution", 20.3)
        stats = mc.get_timer_stats("execution")
        assert stats["count"] == 2
        assert stats["min"] == 10.5
        assert stats["max"] == 20.3
        assert abs(stats["avg"] - 15.4) < 0.01

    def test_get_timer_stats_nonexistent(self):
        mc = MetricsCollector()
        stats = mc.get_timer_stats("nonexistent")
        assert stats == {"count": 0, "min": 0, "max": 0, "avg": 0}

    def test_snapshot(self):
        mc = MetricsCollector()
        mc.increment("actions_total")
        mc.record_duration("execution", 5.0)
        snap = mc.snapshot()
        assert snap["counters"]["actions_total"] == 1
        assert snap["timers"]["execution"]["count"] == 1
        assert snap["timers"]["execution"]["min"] == 5.0

    def test_reset(self):
        mc = MetricsCollector()
        mc.increment("test")
        mc.record_duration("test", 1.0)
        mc.reset()
        assert mc.get_counter("test") == 0
        assert mc.get_timer_stats("test")["count"] == 0

    def test_thread_safety(self):
        mc = MetricsCollector()
        errors = []

        def worker():
            try:
                for _ in range(100):
                    mc.increment("concurrent")
                    mc.record_duration("latency", 1.0)
            except (RuntimeError, ValueError) as e:
                errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == []
        assert mc.get_counter("concurrent") == 1000
        assert mc.get_timer_stats("latency")["count"] == 1000

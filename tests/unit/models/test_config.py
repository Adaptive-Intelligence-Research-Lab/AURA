"""Tests for Config model — AURA-SPEC-010."""
from aura.models.config import (
    AuraConfig,
    EventBusConfig,
    ExecutionConfig,
    GovernanceConfig,
    ObservabilityConfig,
    RuntimeConfig,
)


class TestRuntimeConfig:
    def test_defaults(self):
        config = RuntimeConfig()
        assert config.name == "aura"
        assert config.version == "0.1.0"


class TestEventBusConfig:
    def test_defaults(self):
        config = EventBusConfig()
        assert config.queue_size == 1000


class TestObservabilityConfig:
    def test_defaults(self):
        config = ObservabilityConfig()
        assert config.logging is True
        assert config.metrics is True


class TestGovernanceConfig:
    def test_defaults(self):
        config = GovernanceConfig()
        assert config.default_policy == "allow"


class TestExecutionConfig:
    def test_defaults(self):
        config = ExecutionConfig()
        assert config.default_timeout_ms == 30000
        assert config.max_retry_count == 3


class TestAuraConfig:
    def test_defaults(self):
        config = AuraConfig()
        assert config.runtime.name == "aura"
        assert config.event_bus.queue_size == 1000
        assert config.observability.logging is True
        assert config.governance.default_policy == "allow"
        assert config.execution.default_timeout_ms == 30000

    def test_from_dict(self):
        data = {
            "runtime": {"name": "test", "version": "0.0.1"},
            "event_bus": {"queue_size": 500},
            "observability": {"logging": False, "metrics": False},
            "governance": {"default_policy": "deny"},
            "execution": {"default_timeout_ms": 10000, "max_retry_count": 1},
        }
        config = AuraConfig.from_dict(data)
        assert config.runtime.name == "test"
        assert config.runtime.version == "0.0.1"
        assert config.event_bus.queue_size == 500
        assert config.observability.logging is False
        assert config.governance.default_policy == "deny"
        assert config.execution.default_timeout_ms == 10000

    def test_from_dict_partial(self):
        data = {"runtime": {"name": "partial"}}
        config = AuraConfig.from_dict(data)
        assert config.runtime.name == "partial"
        assert config.event_bus.queue_size == 1000  # default
        assert config.execution.default_timeout_ms == 30000  # default

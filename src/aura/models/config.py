"""
Configuration Model — AURA-SPEC-010

Structured configuration with layered precedence.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
import yaml


@dataclass
class RuntimeConfig:
    name: str = "aura"
    version: str = "0.1.0"


@dataclass
class EventBusConfig:
    queue_size: int = 1000


@dataclass
class ObservabilityConfig:
    logging: bool = True
    metrics: bool = True


@dataclass
class GovernanceConfig:
    default_policy: str = "allow"


@dataclass
class AuraConfig:
    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)
    event_bus: EventBusConfig = field(default_factory=EventBusConfig)
    observability: ObservabilityConfig = field(default_factory=ObservabilityConfig)
    governance: GovernanceConfig = field(default_factory=GovernanceConfig)

    @classmethod
    def from_dict(cls, data: dict) -> "AuraConfig":
        """Create config from dictionary."""
        return cls(
            runtime=RuntimeConfig(**data.get("runtime", {})),
            event_bus=EventBusConfig(**data.get("event_bus", {})),
            observability=ObservabilityConfig(**data.get("observability", {})),
            governance=GovernanceConfig(**data.get("governance", {}))
        )

    @classmethod
    def from_file(cls, path: str) -> "AuraConfig":
        """Load configuration from YAML file."""
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)
"""core.sleep — Async sleep for testing scheduling."""
from __future__ import annotations

import asyncio
from typing import Any

from ...models.capabilities import CapabilityMetadata, CapabilityProvider, RiskLevel


class SleepProvider(CapabilityProvider):
    @property
    def metadata(self) -> CapabilityMetadata:
        return CapabilityMetadata(
            id="core.sleep",
            version="1.0.0",
            name="Sleep",
            description="Sleeps for a specified duration in milliseconds",
            input_schema={"duration_ms": {"type": "integer", "minimum": 0}},
            output_schema={"slept_ms": {"type": "number"}},
            permissions=[],
            risk_level=RiskLevel.LOW,
        )

    def validate(self, parameters: dict[str, Any]) -> dict[str, Any]:
        if "duration_ms" not in parameters:
            raise ValueError("Missing required parameter: duration_ms")
        duration = parameters["duration_ms"]
        if not isinstance(duration, (int, float)):
            raise TypeError("Parameter 'duration_ms' must be a number")
        if duration < 0:
            raise ValueError("Parameter 'duration_ms' must be non-negative")
        return {"duration_ms": float(duration)}

    async def execute(self, parameters: dict[str, Any]) -> dict[str, Any]:
        duration_ms = parameters["duration_ms"]
        await asyncio.sleep(duration_ms / 1000)
        return {"slept_ms": duration_ms}

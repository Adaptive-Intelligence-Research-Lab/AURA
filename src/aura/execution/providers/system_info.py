"""core.system_info — Returns runtime environment information."""
from __future__ import annotations

import os
import platform
import sys
from typing import Any

from ...models.capabilities import CapabilityMetadata, CapabilityProvider, RiskLevel


class SystemInfoProvider(CapabilityProvider):
    @property
    def metadata(self) -> CapabilityMetadata:
        return CapabilityMetadata(
            id="core.system_info",
            version="1.0.0",
            name="System Info",
            description="Returns basic runtime environment information",
            input_schema={},
            output_schema={
                "platform": {"type": "string"},
                "python_version": {"type": "string"},
                "process_id": {"type": "integer"},
                "runtime_version": {"type": "string"},
            },
            permissions=[],
            risk_level=RiskLevel.MINIMAL,
        )

    def validate(self, parameters: dict[str, Any]) -> dict[str, Any]:
        return {}

    async def execute(self, parameters: dict[str, Any]) -> dict[str, Any]:
        return {
            "platform": platform.system(),
            "python_version": sys.version,
            "process_id": os.getpid(),
            "runtime_version": "0.1.0",
        }

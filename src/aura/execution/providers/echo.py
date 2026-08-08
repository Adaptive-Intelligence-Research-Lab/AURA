"""core.echo — Echoes input message back."""
from __future__ import annotations

from typing import Any

from ...models.capabilities import CapabilityMetadata, CapabilityProvider, RiskLevel


class EchoProvider(CapabilityProvider):
    @property
    def metadata(self) -> CapabilityMetadata:
        return CapabilityMetadata(
            id="core.echo",
            version="1.0.0",
            name="Echo",
            description="Echoes the input message back",
            input_schema={"message": {"type": "string"}},
            output_schema={"message": {"type": "string"}},
            permissions=[],
            risk_level=RiskLevel.MINIMAL,
        )

    def validate(self, parameters: dict[str, Any]) -> dict[str, Any]:
        if "message" not in parameters:
            raise ValueError("Missing required parameter: message")
        if not isinstance(parameters["message"], str):
            raise TypeError("Parameter 'message' must be a string")
        return {"message": parameters["message"]}

    async def execute(self, parameters: dict[str, Any]) -> dict[str, Any]:
        return {"message": parameters["message"]}

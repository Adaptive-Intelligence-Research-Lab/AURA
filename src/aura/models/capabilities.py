"""
Capability Model — AURA-SPEC-001

A capability is an abstract description of an operation that the runtime
is able to perform. Capabilities describe "what" may be accomplished,
not "how" the operation is implemented.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class RiskLevel(str, Enum):
    """Security risk classification for a capability."""
    MINIMAL = "minimal"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class CapabilityMetadata:
    """
    Immutable metadata describing a capability.

    This metadata is used by the runtime for:
    - Capability discovery and resolution
    - Governance decisions
    - Observability and documentation
    """
    id: str
    version: str
    name: str
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    permissions: list[str]
    risk_level: RiskLevel
    metadata: dict[str, Any] = field(default_factory=dict)


class CapabilityProvider(ABC):
    """
    Abstract base class defining the contract for capability providers.

    A capability provider implements:
    - metadata: Static description of the capability
    - validate(): Validate input parameters
    - execute(): Perform the capability operation

    The provider SHALL NOT directly manipulate runtime state.
    Instead, it returns structured output which the runtime
    uses to update state and publish events.
    """

    @property
    @abstractmethod
    def metadata(self) -> CapabilityMetadata:
        """Return static capability metadata."""
        ...

    @abstractmethod
    def validate(self, parameters: dict[str, Any]) -> dict[str, Any]:
        """
        Validate and normalize input parameters.

        Args:
            parameters: Raw input parameters

        Returns:
            Validated and normalized parameters

        Raises:
            ValidationError: If parameters are invalid
        """
        ...

    @abstractmethod
    async def execute(self, parameters: dict[str, Any]) -> dict[str, Any]:
        """
        Execute the capability operation.

        Args:
            parameters: Validated input parameters

        Returns:
            Output dictionary matching output_schema

        Note:
            This method MUST NOT directly modify runtime state.
            The runtime kernel wraps the result and handles
            state transitions and event publication.
        """
        ...
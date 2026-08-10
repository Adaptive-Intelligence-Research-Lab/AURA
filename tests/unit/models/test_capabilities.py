"""Tests for Capability model — AURA-SPEC-001."""
import pytest

from aura.models.capabilities import (
    CapabilityMetadata,
    CapabilityProvider,
    RiskLevel,
)


class TestRiskLevel:
    def test_all_values(self):
        assert RiskLevel.MINIMAL == "minimal"
        assert RiskLevel.LOW == "low"
        assert RiskLevel.MODERATE == "moderate"
        assert RiskLevel.HIGH == "high"
        assert RiskLevel.CRITICAL == "critical"

    def test_enum_members(self):
        assert len(RiskLevel) == 5


class TestCapabilityMetadata:
    def test_frozen_dataclass(self):
        meta = CapabilityMetadata(
            id="core.echo",
            version="1.0.0",
            name="Echo",
            description="Echoes input",
            input_schema={"message": {"type": "string"}},
            output_schema={"message": {"type": "string"}},
            permissions=[],
            risk_level=RiskLevel.MINIMAL,
        )
        assert meta.id == "core.echo"
        assert meta.version == "1.0.0"
        assert meta.risk_level == RiskLevel.MINIMAL

    def test_immutability(self):
        meta = CapabilityMetadata(
            id="core.echo",
            version="1.0.0",
            name="Echo",
            description="Echoes input",
            input_schema={},
            output_schema={},
            permissions=[],
            risk_level=RiskLevel.MINIMAL,
        )
        with pytest.raises(AttributeError):
            meta.id = "core.other"  # type: ignore[misc]

    def test_with_permissions(self):
        meta = CapabilityMetadata(
            id="core.secure",
            version="1.0.0",
            name="Secure",
            description="Requires auth",
            input_schema={},
            output_schema={},
            permissions=["admin", "read"],
            risk_level=RiskLevel.HIGH,
        )
        assert meta.permissions == ["admin", "read"]

    def test_with_metadata(self):
        meta = CapabilityMetadata(
            id="core.echo",
            version="1.0.0",
            name="Echo",
            description="Echoes input",
            input_schema={},
            output_schema={},
            permissions=[],
            risk_level=RiskLevel.MINIMAL,
            metadata={"author": "test"},
        )
        assert meta.metadata == {"author": "test"}


class TestCapabilityProvider:
    def test_cannot_instantiate_abstract(self):
        with pytest.raises(TypeError):
            CapabilityProvider()  # type: ignore[abstract]

    def test_subclass_must_implement_all(self):
        class IncompleteProvider(CapabilityProvider):
            pass

        with pytest.raises(TypeError):
            IncompleteProvider()  # type: ignore[abstract]

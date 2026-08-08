"""Tests for the Governance Gate."""
import pytest

from aura.runtime.governance.gate import GovernanceGate, GovernanceDecision
from aura.models.actions import Action


class TestGovernanceGate:
    """Tests for GovernanceGate."""

    def test_default_allow_policy(self):
        """Default policy is allow."""
        gate = GovernanceGate(default_policy="allow")
        action = Action(capability_id="core.echo", parameters={})
        decision = gate.check(action)
        assert decision.allowed is True

    def test_default_deny_policy(self):
        """Default policy can be deny."""
        gate = GovernanceGate(default_policy="deny")
        action = Action(capability_id="core.echo", parameters={})
        decision = gate.check(action)
        assert decision.allowed is False

    def test_explicit_deny(self):
        """Explicit deny overrides default allow."""
        gate = GovernanceGate(default_policy="allow")
        gate.deny_capability("core.dangerous")
        action = Action(capability_id="core.dangerous", parameters={})
        decision = gate.check(action)
        assert decision.allowed is False
        assert "explicitly denied" in decision.reason

    def test_explicit_allow_overrides_deny(self):
        """Explicit allow list takes precedence over deny."""
        gate = GovernanceGate(default_policy="deny")
        gate.deny_capability("core.echo")
        gate.allow_capability("core.echo")
        action = Action(capability_id="core.echo", parameters={})
        decision = gate.check(action)
        assert decision.allowed is True

    def test_invalid_policy_raises(self):
        """Invalid default policy raises ValueError."""
        with pytest.raises(ValueError):
            GovernanceGate(default_policy="invalid")

    def test_multiple_capability_denials(self):
        """Multiple capabilities can be denied."""
        gate = GovernanceGate(default_policy="allow")
        gate.deny_capability("bad.one")
        gate.deny_capability("bad.two")

        action_a = Action(capability_id="bad.one", parameters={})
        action_b = Action(capability_id="bad.two", parameters={})
        action_c = Action(capability_id="good.one", parameters={})

        assert gate.check(action_a).allowed is False
        assert gate.check(action_b).allowed is False
        assert gate.check(action_c).allowed is True

    def test_governance_decision_is_dataclass(self):
        """GovernanceDecision is a proper frozen dataclass."""
        decision = GovernanceDecision(allowed=True, reason="test")
        assert decision.allowed is True
        assert decision.reason == "test"

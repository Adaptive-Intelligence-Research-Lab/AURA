"""Tests for Action model — AURA-SPEC-002."""
from datetime import UTC, datetime
from uuid import UUID

from aura.models.actions import Action, ActionPolicy


class TestActionPolicy:
    def test_default_policy(self):
        policy = ActionPolicy()
        assert policy.timeout_ms == 30000
        assert policy.retry_count == 0

    def test_custom_policy(self):
        policy = ActionPolicy(timeout_ms=5000, retry_count=3)
        assert policy.timeout_ms == 5000
        assert policy.retry_count == 3


class TestAction:
    def test_action_creation_with_required_fields(self):
        action = Action(capability_id="core.echo")
        assert action.capability_id == "core.echo"
        assert action.parameters == {}
        assert isinstance(action.id, UUID)
        isinstance(action.correlation_id, UUID)
        assert isinstance(action.created_at, datetime)
        assert action.created_at.tzinfo is UTC

    def test_action_unique_ids(self):
        a1 = Action(capability_id="core.echo")
        a2 = Action(capability_id="core.echo")
        assert a1.id != a2.id

    def test_action_correlation_id_unique(self):
        a1 = Action(capability_id="core.echo")
        a2 = Action(capability_id="core.echo")
        assert a1.correlation_id != a2.correlation_id

    def test_action_with_parameters(self):
        action = Action(
            capability_id="core.echo",
            parameters={"message": "hello"},
        )
        assert action.parameters == {"message": "hello"}

    def test_action_with_context(self):
        action = Action(
            capability_id="core.echo",
            context={"user_id": "123"},
        )
        assert action.context == {"user_id": "123"}

    def test_action_with_metadata(self):
        action = Action(
            capability_id="core.echo",
            metadata={"source": "test"},
        )
        assert action.metadata == {"source": "test"}

    def test_action_with_custom_policy(self):
        policy = ActionPolicy(timeout_ms=5000)
        action = Action(
            capability_id="core.echo",
            execution_policy=policy,
        )
        assert action.execution_policy.timeout_ms == 5000

    def test_action_created_at_is_recent(self):
        before = datetime.now(UTC)
        action = Action(capability_id="core.echo")
        after = datetime.now(UTC)
        assert before <= action.created_at <= after

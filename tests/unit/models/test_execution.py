"""Tests for ExecutionResult model — AURA-SPEC-002."""
from datetime import UTC, datetime
from uuid import UUID

from aura.models.execution import ExecutionResult, ExecutionStatus


class TestExecutionStatus:
    def test_all_values(self):
        assert ExecutionStatus.SUCCESS == "success"
        assert ExecutionStatus.FAILURE == "failure"
        assert ExecutionStatus.TIMEOUT == "timeout"
        assert ExecutionStatus.CANCELLED == "cancelled"

    def test_enum_count(self):
        assert len(ExecutionStatus) == 4


class TestExecutionResult:
    def test_success_result(self):
        result = ExecutionResult(
            action_id=UUID("00000000-0000-0000-0000-000000000001"),
            status=ExecutionStatus.SUCCESS,
            capability_id="core.echo",
            output={"message": "hello"},
        )
        assert result.success is True
        assert result.output == {"message": "hello"}
        assert result.error is None

    def test_failure_result(self):
        result = ExecutionResult(
            action_id=UUID("00000000-0000-0000-0000-000000000001"),
            status=ExecutionStatus.FAILURE,
            capability_id="core.echo",
            error="Something went wrong",
        )
        assert result.success is False
        assert result.error == "Something went wrong"

    def test_execution_id_auto_generated(self):
        r1 = ExecutionResult(
            action_id=UUID("00000000-0000-0000-0000-000000000001"),
            status=ExecutionStatus.SUCCESS,
        )
        r2 = ExecutionResult(
            action_id=UUID("00000000-0000-0000-0000-000000000001"),
            status=ExecutionStatus.SUCCESS,
        )
        assert r1.execution_id != r2.execution_id

    def test_started_at_auto_set(self):
        before = datetime.now(UTC)
        result = ExecutionResult(
            action_id=UUID("00000000-0000-0000-0000-000000000001"),
            status=ExecutionStatus.SUCCESS,
        )
        after = datetime.now(UTC)
        assert before <= result.started_at <= after

    def test_completed_at_optional(self):
        result = ExecutionResult(
            action_id=UUID("00000000-0000-0000-0000-000000000001"),
            status=ExecutionStatus.SUCCESS,
        )
        assert result.completed_at is None

    def test_metadata(self):
        result = ExecutionResult(
            action_id=UUID("00000000-0000-0000-0000-000000000001"),
            status=ExecutionStatus.SUCCESS,
            metadata={"duration_ms": 1.5},
        )
        assert result.metadata["duration_ms"] == 1.5

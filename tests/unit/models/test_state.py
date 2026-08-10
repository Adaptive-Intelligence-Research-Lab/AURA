"""Tests for State model — AURA-SPEC-009."""

from aura.models.state import ActionState, KernelState, StateTransitionError


class TestActionState:
    def test_all_states(self):
        assert ActionState.CREATED == "created"
        assert ActionState.VALIDATED == "validated"
        assert ActionState.QUEUED == "queued"
        assert ActionState.RUNNING == "running"
        assert ActionState.COMPLETED == "completed"
        assert ActionState.FAILED == "failed"
        assert ActionState.CANCELLED == "cancelled"

    def test_seven_states(self):
        assert len(ActionState) == 7


class TestKernelState:
    def test_all_states(self):
        assert KernelState.CREATED == "created"
        assert KernelState.INITIALIZING == "initializing"
        assert KernelState.READY == "ready"
        assert KernelState.EXECUTING == "executing"
        assert KernelState.SHUTTING_DOWN == "shutting_down"
        assert KernelState.STOPPED == "stopped"
        assert KernelState.INITIALIZATION_FAILED == "initialization_failed"

    def test_seven_states(self):
        assert len(KernelState) == 7


class TestStateTransitionError:
    def test_is_exception(self):
        error = StateTransitionError("test")
        assert isinstance(error, Exception)
        assert str(error) == "test"

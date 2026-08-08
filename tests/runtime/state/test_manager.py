"""Tests for State Manager."""
from uuid import uuid4

import pytest

from aura.models.events import Event, EventType
from aura.models.state import ActionState, KernelState, StateTransitionError
from aura.runtime.state.manager import StateManager


class TestStateManager:
    """Tests for StateManager."""

    @pytest.mark.asyncio
    async def test_action_lifecycle(self):
        """Full action lifecycle through event handling."""
        sm = StateManager()
        action_id = str(uuid4())

        # CREATED
        await sm.handle_event(Event(
            event_type=EventType.ACTION_CREATED,
            source="test",
            payload={"action_id": action_id}
        ))
        assert sm.get_state(action_id) == ActionState.CREATED

        # VALIDATED
        await sm.handle_event(Event(
            event_type=EventType.ACTION_VALIDATED,
            source="test",
            payload={"action_id": action_id}
        ))
        assert sm.get_state(action_id) == ActionState.VALIDATED

        # RUNNING (from VALIDATED - v0.1 simplification)
        await sm.handle_event(Event(
            event_type=EventType.ACTION_STARTED,
            source="test",
            payload={"action_id": action_id}
        ))
        assert sm.get_state(action_id) == ActionState.RUNNING

        # COMPLETED
        await sm.handle_event(Event(
            event_type=EventType.ACTION_COMPLETED,
            source="test",
            payload={"action_id": action_id}
        ))
        assert sm.get_state(action_id) == ActionState.COMPLETED

    @pytest.mark.asyncio
    async def test_invalid_transition_rejected(self):
        """Invalid transitions raise StateTransitionError."""
        sm = StateManager()
        action_id = str(uuid4())

        # Direct CREATED -> COMPLETED should fail
        with pytest.raises(StateTransitionError):
            await sm.handle_event(Event(
                event_type=EventType.ACTION_COMPLETED,
                source="test",
                payload={"action_id": action_id}
            ))

    @pytest.mark.asyncio
    async def test_state_persistence(self):
        """State should persist across events."""
        sm = StateManager()
        action_id = str(uuid4())

        await sm.handle_event(Event(
            event_type=EventType.ACTION_CREATED,
            source="test",
            payload={"action_id": action_id}
        ))

        # State should be retrievable
        assert sm.get_state(action_id) == ActionState.CREATED

    def test_set_initial_state(self):
        """set_initial_state creates CREATED state."""
        sm = StateManager()
        state = sm.set_initial_state("test-id")
        assert state == ActionState.CREATED
        assert sm.get_state("test-id") == ActionState.CREATED

    def test_clear_state(self):
        """clear_state removes tracking."""
        sm = StateManager()
        sm.set_initial_state("test-id")
        assert sm.clear_state("test-id") is True
        assert sm.get_state("test-id") is None

    def test_clear_nonexistent_state(self):
        """clear_state returns False for unknown action."""
        sm = StateManager()
        assert sm.clear_state("nonexistent") is False

    @pytest.mark.asyncio
    async def test_kernel_state_runtime_started(self):
        """RUNTIME_STARTED transitions kernel to READY."""
        sm = StateManager()
        await sm.handle_event(Event(
            event_type=EventType.RUNTIME_STARTED,
            source="kernel",
            payload={}
        ))
        assert sm.get_kernel_state() == KernelState.READY

    @pytest.mark.asyncio
    async def test_kernel_state_runtime_stopped(self):
        """RUNTIME_STOPPED transitions kernel to STOPPED."""
        sm = StateManager()
        await sm.handle_event(Event(
            event_type=EventType.RUNTIME_STOPPED,
            source="kernel",
            payload={}
        ))
        assert sm.get_kernel_state() == KernelState.STOPPED

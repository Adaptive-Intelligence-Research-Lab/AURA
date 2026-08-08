"""
Runtime State Manager — AURA-008

The State Manager consumes runtime events and maintains 
the lifecycle state of runtime entities.

The State Manager SHALL be event-driven.
It SHALL NOT directly control execution.

Example:
  ActionStarted
       ->
  StateManager
       ->
  ActionState = RUNNING
"""
from __future__ import annotations

import logging

from ...models.events import Event, EventType
from ...models.state import ActionState, KernelState, StateTransitionError

logger = logging.getLogger(__name__)


_VALID_ACTION_TRANSITIONS: dict[ActionState, set[ActionState]] = {
    ActionState.CREATED: {ActionState.VALIDATED, ActionState.FAILED},
    ActionState.VALIDATED: {ActionState.QUEUED, ActionState.FAILED},
    ActionState.QUEUED: {ActionState.RUNNING, ActionState.FAILED, ActionState.CANCELLED},
    ActionState.RUNNING: {ActionState.COMPLETED, ActionState.FAILED},
    ActionState.COMPLETED: set(),
    ActionState.FAILED: {ActionState.CREATED},  # For retries
    ActionState.CANCELLED: set(),
}


class StateManager:
    """
    Maintains runtime entity state through event consumption.
    
    State transitions are event-driven and must follow
    defined transition rules. Invalid transitions produce
    structured runtime errors.
    
    Implements the async callable interface for use 
    with the Event Bus.
    """

    def __init__(self):
        """Initialize the state manager."""
        self._action_states: dict[str, ActionState] = {}
        self._kernel_state: KernelState = KernelState.CREATED

    async def handle_event(self, event: Event) -> ActionState | None:
        """
        Process an event and update state accordingly.
        
        This method is async to comply with the Event Bus
        subscriber contract.

        Args:
            event: The runtime event to process

        Returns:
            The updated state for the entity, or None if not applicable

        Raises:
            StateTransitionError: If an invalid transition is attempted
        """
        action_id = event.payload.get("action_id")

        if event.event_type == EventType.ACTION_CREATED:
            return self._handle_action_created(action_id)

        elif event.event_type == EventType.ACTION_VALIDATED:
            self._transition_action(action_id, ActionState.VALIDATED)
            # In v0.1, validation implies immediate queueing (no external queue)
            return self._transition_action(action_id, ActionState.QUEUED)

        elif event.event_type == EventType.ACTION_STARTED:
            return self._transition_action(action_id, ActionState.RUNNING)

        elif event.event_type == EventType.ACTION_COMPLETED:
            return self._transition_action(action_id, ActionState.COMPLETED)

        elif event.event_type == EventType.ACTION_FAILED:
            return self._transition_action(action_id, ActionState.FAILED)

        elif event.event_type == EventType.CAPABILITY_REGISTERED:
            logger.debug("Capability registered")
            return None

        elif event.event_type == EventType.CAPABILITY_UNREGISTERED:
            logger.debug("Capability unregistered")
            return None

        elif event.event_type == EventType.RUNTIME_STARTED:
            self._kernel_state = KernelState.READY
            return None

        elif event.event_type == EventType.RUNTIME_STOPPED:
            self._kernel_state = KernelState.STOPPED
            return None

        logger.debug(f"Unhandled event type: {event.event_type}")
        return None

    def _handle_action_created(self, action_id: str | None) -> ActionState:
        """Handle ActionCreated event."""
        if not action_id:
            return ActionState.CREATED

        # Always set to CREATED (supports retries from FAILED state)
        self._action_states[action_id] = ActionState.CREATED

        return ActionState.CREATED

    def _transition_action(
        self, action_id: str | None, target: ActionState
    ) -> ActionState:
        """
        Attempt a state transition for an action.

        Args:
            action_id: The action ID string
            target: The target state

        Returns:
            The new state

        Raises:
            StateTransitionError: If transition is not permitted
        """
        if not action_id:
            raise StateTransitionError("No action_id in event payload")

        if action_id not in self._action_states:
            self._action_states[action_id] = ActionState.CREATED

        current = self._action_states[action_id]

        # Allow self-transitions
        if current == target:
            return target

        valid_targets = _VALID_ACTION_TRANSITIONS.get(current, set())

        if target not in valid_targets:
            raise StateTransitionError(
                f"Invalid transition: {current.value} -> {target.value} "
                f"for action {action_id}"
            )

        self._action_states[action_id] = target
        logger.debug(
            f"Action {action_id} state: {current.value} -> {target.value}"
        )
        return target

    def get_state(self, action_id: str) -> ActionState | None:
        """
        Get current state of an action.

        Args:
            action_id: The action identifier (UUID string)

        Returns:
            Current state, or None if not tracked
        """
        return self._action_states.get(action_id)

    def set_initial_state(self, action_id: str) -> ActionState:
        """
        Set initial state for a new action.

        Args:
            action_id: The action identifier (UUID string)

        Returns:
            The initial CREATED state
        """
        self._action_states[action_id] = ActionState.CREATED
        return ActionState.CREATED

    def get_kernel_state(self) -> KernelState:
        """Get current kernel state."""
        return self._kernel_state

    def clear_state(self, action_id: str) -> bool:
        """
        Remove state tracking for an action.

        Args:
            action_id: The action identifier

        Returns:
            True if state was removed, False if not tracked
        """
        if action_id in self._action_states:
            del self._action_states[action_id]
            return True
        return False

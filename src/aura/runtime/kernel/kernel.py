"""
Runtime Kernel — AURA-001

The Runtime Kernel is the central orchestrator for the AURA runtime.
It coordinates the EventBus, StateManager, CapabilityRegistry,
GovernanceGate, and CapabilityExecutor to process Actions.

The Kernel SHALL:
- Initialize and manage runtime lifecycle
- Coordinate all runtime components
- Process actions through the execution pipeline
- Emit lifecycle events

Example:
  kernel = RuntimeKernel()
  await kernel.start()
  await kernel.execute(action)
  await kernel.stop()
"""
from __future__ import annotations

import logging
from typing import Optional

from ...models.actions import Action
from ...models.capabilities import CapabilityProvider
from ...models.events import Event, EventType
from ..event_bus.bus import EventBus
from ..executor.executor import CapabilityExecutor, ExecutionResult
from ..governance.gate import GovernanceGate
from ..registry.capabilities import CapabilityRegistry
from ..state.manager import StateManager

logger = logging.getLogger(__name__)


class RuntimeKernel:
    """
    Central orchestrator for the AURA Runtime Core.

    The Kernel maintains references to all core runtime
    components and coordinates their interaction.

    Lifecycle:
        CREATED -> INITIALIZING -> READY -> STOPPED
    """

    def __init__(self):
        """Initialize the runtime kernel with all subsystems."""
        self._event_bus = EventBus()
        self._state_manager = StateManager()
        self._governance = GovernanceGate()
        self._registry = CapabilityRegistry()
        self._executor = CapabilityExecutor(
            event_bus=self._event_bus,
            governance=self._governance,
        )
        self._initialized: bool = False

    @property
    def event_bus(self) -> EventBus:
        """Get the runtime event bus."""
        return self._event_bus

    @property
    def state_manager(self) -> StateManager:
        """Get the state manager."""
        return self._state_manager

    @property
    def governance(self) -> GovernanceGate:
        """Get the governance gate."""
        return self._governance

    @property
    def registry(self) -> CapabilityRegistry:
        """Get the capability registry."""
        return self._registry

    @property
    def executor(self) -> CapabilityExecutor:
        """Get the capability executor."""
        return self._executor

    async def start(self) -> None:
        """
        Start the runtime kernel.

        Initializes the event bus and subscribes the
        state manager to relevant events.

        Raises:
            RuntimeError: If already initialized
        """
        if self._initialized:
            raise RuntimeError("Runtime kernel already initialized")

        logger.info("Starting AURA Runtime Kernel...")

        await self._event_bus.start()

        # Subscribe state manager to all action lifecycle events
        self._event_bus.subscribe(
            EventType.ACTION_CREATED, self._state_manager.handle_event
        )
        self._event_bus.subscribe(
            EventType.ACTION_VALIDATED, self._state_manager.handle_event
        )
        self._event_bus.subscribe(
            EventType.ACTION_STARTED, self._state_manager.handle_event
        )
        self._event_bus.subscribe(
            EventType.ACTION_COMPLETED, self._state_manager.handle_event
        )
        self._event_bus.subscribe(
            EventType.ACTION_FAILED, self._state_manager.handle_event
        )
        self._event_bus.subscribe(
            EventType.RUNTIME_STARTED, self._state_manager.handle_event
        )
        self._event_bus.subscribe(
            EventType.RUNTIME_STOPPED, self._state_manager.handle_event
        )
        self._event_bus.subscribe(
            EventType.CAPABILITY_REGISTERED, self._state_manager.handle_event
        )
        self._event_bus.subscribe(
            EventType.CAPABILITY_UNREGISTERED, self._state_manager.handle_event
        )

        # Publish runtime started event
        await self._event_bus.publish(Event(
            event_type=EventType.RUNTIME_STARTED,
            source="kernel",
            payload={},
        ))

        self._initialized = True
        logger.info("AURA Runtime Kernel started")

    async def execute(self, action: Action) -> ExecutionResult:
        """
        Execute an action.

        The kernel validates the action, resolves the
        capability, and delegates to the executor.

        Args:
            action: The action to execute

        Returns:
            ExecutionResult with outcome of execution

        Raises:
            ValueError: If capability not registered
            RuntimeError: If kernel not started
        """
        if not self._initialized:
            raise RuntimeError("Runtime kernel not started")

        cap_id = action.capability_id

        if not self._registry.contains(cap_id):
            raise ValueError(
                f"Capability not registered: {cap_id}"
            )

        provider = self._registry.resolve(cap_id)

        # Publish action created event
        await self._event_bus.publish(Event(
            event_type=EventType.ACTION_CREATED,
            source="kernel",
            payload={
                "action_id": str(action.id),
                "capability_id": cap_id,
            },
        ))

        # Execute through executor
        result = await self._executor.execute(action, provider)

        return result

    async def register_capability(self, provider: CapabilityProvider) -> None:
        """
        Register a capability provider.

        Args:
            provider: The capability provider to register

        Raises:
            ValueError: If capability already registered
        """
        self._registry.register(provider)

        # Publish registration event
        await self._event_bus.publish(Event(
            event_type=EventType.CAPABILITY_REGISTERED,
            source="kernel",
            payload={
                "capability_id": provider.metadata.id,
            },
        ))

    async def stop(self) -> None:
        """
        Stop the runtime kernel.

        Stops the event bus and cleans up resources.
        """
        if not self._initialized:
            return

        logger.info("Stopping AURA Runtime Kernel...")

        await self._event_bus.publish(Event(
            event_type=EventType.RUNTIME_STOPPED,
            source="kernel",
            payload={},
        ))

        await self._event_bus.stop()
        self._initialized = False
        logger.info("AURA Runtime Kernel stopped")

    def get_state(self, action_id: str) -> Optional[object]:
        """
        Get the current state of an action.

        Args:
            action_id: The action identifier

        Returns:
            Current ActionState, or None
        """
        return self._state_manager.get_state(action_id)

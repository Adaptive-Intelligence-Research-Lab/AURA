"""
Runtime Kernel — AURA-IMPL-001 §25, §27

The Runtime Kernel is the composition root for the AURA runtime.
It coordinates EventBus, StateManager, CapabilityRegistry,
GovernanceGate, and CapabilityExecutor.

Public API (§27):
    AURARuntime()
    await runtime.initialize()
    await runtime.start()
    result = await runtime.execute(action)
    health = await runtime.health()
    await runtime.stop()
"""
from __future__ import annotations

import logging
import uuid
from typing import Self

from ..execution.executor import CapabilityExecutor
from ..models.actions import Action
from ..models.capabilities import CapabilityProvider
from ..models.events import Event, EventType
from ..models.execution import ExecutionResult
from .event_bus.bus import EventBus
from .governance.gate import GovernanceGate
from .registry.capabilities import CapabilityRegistry
from .state.manager import StateManager

logger = logging.getLogger(__name__)


class AURARuntime:
    """
    Central orchestrator for the AURA Runtime Core.

    Lifecycle (§26):
        CREATED → INITIALIZING → READY → EXECUTING → READY → SHUTTING_DOWN → STOPPED
    """

    def __init__(self) -> None:
        self._event_bus: EventBus | None = None
        self._state_manager: StateManager | None = None
        self._governance: GovernanceGate | None = None
        self._registry: CapabilityRegistry | None = None
        self._executor: CapabilityExecutor | None = None
        self._initialized: bool = False
        self._started: bool = False
        self._runtime_id: uuid.UUID = uuid.uuid4()

    async def __aenter__(self) -> Self:
        await self.initialize()
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.stop()

    # --- Properties ---

    @property
    def event_bus(self) -> EventBus:
        assert self._event_bus is not None, "Call initialize() first"
        return self._event_bus

    @property
    def state_manager(self) -> StateManager:
        assert self._state_manager is not None, "Call initialize() first"
        return self._state_manager

    @property
    def governance(self) -> GovernanceGate:
        assert self._governance is not None, "Call initialize() first"
        return self._governance

    @property
    def registry(self) -> CapabilityRegistry:
        assert self._registry is not None, "Call initialize() first"
        return self._registry

    @property
    def executor(self) -> CapabilityExecutor:
        assert self._executor is not None, "Call initialize() first"
        return self._executor

    # --- Lifecycle API (§27) ---

    async def initialize(self) -> None:
        """Initialize all runtime subsystems."""
        if self._initialized:
            raise RuntimeError("AURARuntime already initialized")

        self._event_bus = EventBus()
        self._state_manager = StateManager()
        self._governance = GovernanceGate()
        self._registry = CapabilityRegistry()
        self._executor = CapabilityExecutor(
            event_bus=self._event_bus,
            governance=self._governance,
        )
        self._initialized = True

    async def start(self) -> None:
        """Start event infrastructure."""
        if not self._initialized:
            raise RuntimeError("Call initialize() before start()")
        if self._started:
            raise RuntimeError("AURARuntime already started")

        for event_type in (
            EventType.ACTION_CREATED,
            EventType.ACTION_VALIDATED,
            EventType.ACTION_STARTED,
            EventType.ACTION_COMPLETED,
            EventType.ACTION_FAILED,
            EventType.RUNTIME_STARTED,
            EventType.RUNTIME_STOPPED,
            EventType.CAPABILITY_REGISTERED,
            EventType.CAPABILITY_UNREGISTERED,
        ):
            self.event_bus.subscribe(event_type, self.state_manager.handle_event)

        await self.event_bus.start()

        await self.event_bus.publish(Event(
            event_type=EventType.RUNTIME_STARTED,
            source="kernel",
            payload={"runtime_id": str(self._runtime_id)},
        ))

        self._started = True

    async def execute(self, action: Action) -> ExecutionResult:
        """Execute an action through the full pipeline."""
        if not self._started:
            raise RuntimeError("AURARuntime not started. Call start() first.")

        cap_id = action.capability_id
        if not self.registry.contains(cap_id):
            raise ValueError(f"Capability not registered: {cap_id}")

        provider = self.registry.resolve(cap_id)

        await self.event_bus.publish(Event(
            event_type=EventType.ACTION_CREATED,
            source="kernel",
            payload={
                "action_id": str(action.id),
                "capability_id": cap_id,
            },
            correlation_id=action.correlation_id,
        ))

        result = await self.executor.execute(action, provider)
        return result

    async def register_capability(self, provider: CapabilityProvider) -> None:
        """Register a capability provider."""
        self.registry.register(provider)

        await self.event_bus.publish(Event(
            event_type=EventType.CAPABILITY_REGISTERED,
            source="kernel",
            payload={"capability_id": provider.metadata.id},
        ))

    async def health(self) -> dict:
        """Return runtime health status (§27)."""
        return {
            "status": "ready" if self._started else "stopped",
            "initialized": self._initialized,
            "started": self._started,
            "runtime_id": str(self._runtime_id),
            "kernel_state": self.state_manager.get_kernel_state().value,
            "capabilities": self.registry.list(),
        }

    async def stop(self) -> None:
        """Gracefully shut down the runtime."""
        if not self._initialized:
            return

        if self._started:
            await self.event_bus.publish(Event(
                event_type=EventType.RUNTIME_STOPPED,
                source="kernel",
                payload={"runtime_id": str(self._runtime_id)},
            ))
            await self.event_bus.stop()
            self._started = False

        self._initialized = False

    def get_state(self, action_id: str) -> object | None:
        """Get current state of an action."""
        return self.state_manager.get_state(action_id)

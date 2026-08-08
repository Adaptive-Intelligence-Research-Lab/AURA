"""
Core Data Models for AURA Runtime Core.

All models are independent from execution implementations.
"""
from .capabilities import CapabilityMetadata, CapabilityProvider, RiskLevel
from .actions import Action, ActionPolicy
from .execution import ExecutionResult, ExecutionStatus
from .state import ActionState, KernelState, StateTransitionError
from .errors import RuntimeError as AURARuntimeError, ErrorCategory, ErrorSeverity
from .config import AuraConfig
from .events import Event, EventType

__all__ = [
    # Capabilities
    "CapabilityMetadata",
    "CapabilityProvider",
    "RiskLevel",
    # Actions
    "Action",
    "ActionPolicy",
    # Execution
    "ExecutionResult",
    "ExecutionStatus",
    # State
    "ActionState",
    "KernelState",
    "StateTransitionError",
    # Errors
    "AURARuntimeError",
    "ErrorCategory",
    "ErrorSeverity",
    # Config
    "AuraConfig",
    # Events
    "Event",
    "EventType",
]
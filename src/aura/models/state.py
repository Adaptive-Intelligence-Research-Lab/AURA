"""
Runtime State Model — AURA-SPEC-009

Represents the lifecycle state of runtime entities.
State transitions are explicit and event-driven.
"""
from __future__ import annotations

from enum import Enum


class ActionState(str, Enum):
    """
    Lifecycle states for an Action.

    Transitions SHALL be explicit:
    CREATED -> VALIDATED -> QUEUED -> RUNNING -> COMPLETED/FAILED/CANCELLED
    """
    CREATED = "created"
    VALIDATED = "validated"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class KernelState(str, Enum):
    """
    Lifecycle states for the Runtime Kernel.

    CREATED -> INITIALIZING -> READY -> EXECUTING -> READY ->
    SHUTTING_DOWN -> STOPPED

    Failure during initialization -> INITIALIZATION_FAILED
    """
    CREATED = "created"
    INITIALIZING = "initializing"
    READY = "ready"
    EXECUTING = "executing"
    SHUTTING_DOWN = "shutting_down"
    STOPPED = "stopped"
    INITIALIZATION_FAILED = "initialization_failed"


class StateTransitionError(Exception):
    """
    Raised when an invalid state transition is attempted.

    Example:
        Trying to transition from RUNNING -> QUEUED
    """
    pass
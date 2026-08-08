"""
Runtime Error Model — AURA-SPEC-008

Structured error representation for consistent failure handling.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4
from datetime import datetime, timezone


class ErrorCategory(str, Enum):
    """Classification of error categories."""
    VALIDATION = "validation"
    RUNTIME = "runtime"
    RESOURCE = "resource"
    SECURITY = "security"
    NETWORK = "network"
    EXTENSION = "extension"
    INTERNAL = "internal"


class ErrorSeverity(str, Enum):
    """Severity levels for errors."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class RuntimeError:
    """
    Structured runtime error.

    Errors SHALL:
    - Have a unique Error ID
    - Declare an Error Code
    - Include classification
    - Include context
    - Include recovery metadata
    """
    error_type: str
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    error_id: UUID = field(default_factory=uuid4)
    action_id: Optional[UUID] = None
    capability_id: Optional[str] = None
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    recoverable: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
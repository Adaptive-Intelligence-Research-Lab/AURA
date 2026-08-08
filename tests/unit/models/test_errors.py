"""Tests for Error model — AURA-SPEC-008."""
from datetime import UTC, datetime
from uuid import UUID

from aura.models.errors import (
    ErrorCategory,
    ErrorSeverity,
)
from aura.models.errors import (
    RuntimeError as AURARuntimeError,
)


class TestErrorCategory:
    def test_all_categories(self):
        assert ErrorCategory.VALIDATION == "validation"
        assert ErrorCategory.RUNTIME == "runtime"
        assert ErrorCategory.RESOURCE == "resource"
        assert ErrorCategory.SECURITY == "security"
        assert ErrorCategory.NETWORK == "network"
        assert ErrorCategory.EXTENSION == "extension"
        assert ErrorCategory.INTERNAL == "internal"

    def test_seven_categories(self):
        assert len(ErrorCategory) == 7


class TestErrorSeverity:
    def test_all_severities(self):
        assert ErrorSeverity.DEBUG == "debug"
        assert ErrorSeverity.INFO == "info"
        assert ErrorSeverity.WARNING == "warning"
        assert ErrorSeverity.ERROR == "error"
        assert ErrorSeverity.CRITICAL == "critical"

    def test_five_severities(self):
        assert len(ErrorSeverity) == 5


class TestRuntimeError:
    def test_creation(self):
        error = AURARuntimeError(
            error_type="TestError",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.ERROR,
            message="Something failed",
        )
        assert error.error_type == "TestError"
        assert error.category == ErrorCategory.VALIDATION
        assert error.severity == ErrorSeverity.ERROR
        assert error.message == "Something failed"

    def test_auto_generated_fields(self):
        error = AURARuntimeError(
            error_type="TestError",
            category=ErrorCategory.RUNTIME,
            severity=ErrorSeverity.WARNING,
            message="Warning",
        )
        assert isinstance(error.error_id, UUID)
        assert isinstance(error.timestamp, datetime)
        assert error.timestamp.tzinfo is UTC

    def test_optional_fields(self):
        error = AURARuntimeError(
            error_type="TestError",
            category=ErrorCategory.RUNTIME,
            severity=ErrorSeverity.ERROR,
            message="Error",
        )
        assert error.action_id is None
        assert error.capability_id is None
        assert error.recoverable is True
        assert error.metadata == {}

    def test_with_context(self):
        action_id = UUID("00000000-0000-0000-0000-000000000001")
        error = AURARuntimeError(
            error_type="ExecError",
            category=ErrorCategory.RESOURCE,
            severity=ErrorSeverity.CRITICAL,
            message="Out of memory",
            action_id=action_id,
            capability_id="core.heavy",
            recoverable=False,
            metadata={"heap_mb": 1024},
        )
        assert error.action_id == action_id
        assert error.capability_id == "core.heavy"
        assert error.recoverable is False
        assert error.metadata["heap_mb"] == 1024

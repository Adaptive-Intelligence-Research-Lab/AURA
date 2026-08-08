"""Tests for v0.1 core capability providers."""
import pytest

from aura.execution.providers import EchoProvider, SleepProvider, SystemInfoProvider


class TestEchoProvider:
    def test_metadata(self):
        provider = EchoProvider()
        meta = provider.metadata
        assert meta.id == "core.echo"
        assert meta.version == "1.0.0"
        assert meta.name == "Echo"
        assert meta.risk_level.value == "minimal"
        assert meta.permissions == []

    def test_validate_with_message(self):
        provider = EchoProvider()
        result = provider.validate({"message": "hello"})
        assert result == {"message": "hello"}

    def test_validate_missing_message(self):
        provider = EchoProvider()
        with pytest.raises(ValueError, match="Missing required parameter"):
            provider.validate({})

    def test_validate_non_string_message(self):
        provider = EchoProvider()
        with pytest.raises(TypeError, match="must be a string"):
            provider.validate({"message": 123})

    @pytest.mark.asyncio
    async def test_execute(self):
        provider = EchoProvider()
        result = await provider.execute({"message": "hello AURA"})
        assert result == {"message": "hello AURA"}

    @pytest.mark.asyncio
    async def test_execute_empty_string(self):
        provider = EchoProvider()
        result = await provider.execute({"message": ""})
        assert result == {"message": ""}


class TestSystemInfoProvider:
    def test_metadata(self):
        provider = SystemInfoProvider()
        meta = provider.metadata
        assert meta.id == "core.system_info"
        assert meta.version == "1.0.0"
        assert meta.name == "System Info"
        assert meta.risk_level.value == "minimal"
        assert meta.permissions == []

    def test_validate_empty_params(self):
        provider = SystemInfoProvider()
        result = provider.validate({})
        assert result == {}

    @pytest.mark.asyncio
    async def test_execute_returns_expected_fields(self):
        provider = SystemInfoProvider()
        result = await provider.execute({})
        assert "platform" in result
        assert "python_version" in result
        assert "process_id" in result
        assert "runtime_version" in result

    @pytest.mark.asyncio
    async def test_execute_platform_is_string(self):
        provider = SystemInfoProvider()
        result = await provider.execute({})
        assert isinstance(result["platform"], str)

    @pytest.mark.asyncio
    async def test_execute_process_id_is_int(self):
        provider = SystemInfoProvider()
        result = await provider.execute({})
        assert isinstance(result["process_id"], int)
        assert result["process_id"] > 0

    @pytest.mark.asyncio
    async def test_execute_runtime_version(self):
        provider = SystemInfoProvider()
        result = await provider.execute({})
        assert result["runtime_version"] == "0.1.0"


class TestSleepProvider:
    def test_metadata(self):
        provider = SleepProvider()
        meta = provider.metadata
        assert meta.id == "core.sleep"
        assert meta.version == "1.0.0"
        assert meta.name == "Sleep"
        assert meta.risk_level.value == "low"
        assert meta.permissions == []

    def test_validate_with_duration(self):
        provider = SleepProvider()
        result = provider.validate({"duration_ms": 100})
        assert result == {"duration_ms": 100.0}

    def test_validate_missing_duration(self):
        provider = SleepProvider()
        with pytest.raises(ValueError, match="Missing required parameter"):
            provider.validate({})

    def test_validate_non_number(self):
        provider = SleepProvider()
        with pytest.raises(TypeError, match="must be a number"):
            provider.validate({"duration_ms": "fast"})

    def test_validate_negative_duration(self):
        provider = SleepProvider()
        with pytest.raises(ValueError, match="non-negative"):
            provider.validate({"duration_ms": -100})

    @pytest.mark.asyncio
    async def test_execute(self):
        provider = SleepProvider()
        result = await provider.execute({"duration_ms": 10})
        assert result["slept_ms"] == 10

    @pytest.mark.asyncio
    async def test_execute_zero_duration(self):
        provider = SleepProvider()
        result = await provider.execute({"duration_ms": 0})
        assert result["slept_ms"] == 0

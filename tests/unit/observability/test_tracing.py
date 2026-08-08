"""Tests for TraceContext."""
from uuid import uuid4

from aura.observability.tracing import TraceContext


class TestTraceContext:
    def test_creation_with_correlation_id(self):
        cid = uuid4()
        ctx = TraceContext(correlation_id=cid)
        assert ctx.correlation_id == cid
        assert ctx.action_id is None
        assert ctx.execution_id is None

    def test_creation_with_all_ids(self):
        cid = uuid4()
        aid = uuid4()
        eid = uuid4()
        ctx = TraceContext(correlation_id=cid, action_id=aid, execution_id=eid)
        assert ctx.correlation_id == cid
        assert ctx.action_id == aid
        assert ctx.execution_id == eid

    def test_to_dict(self):
        cid = uuid4()
        aid = uuid4()
        ctx = TraceContext(correlation_id=cid, action_id=aid)
        d = ctx.to_dict()
        assert d["correlation_id"] == str(cid)
        assert d["action_id"] == str(aid)
        assert d["execution_id"] is None

    def test_to_dict_with_execution_id(self):
        cid = uuid4()
        eid = uuid4()
        ctx = TraceContext(correlation_id=cid, execution_id=eid)
        d = ctx.to_dict()
        assert d["execution_id"] == str(eid)

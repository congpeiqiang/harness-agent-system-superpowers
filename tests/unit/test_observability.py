import pytest
from src.observability.logging import setup_logging, get_logger
from src.observability.langsmith_setup import setup_langsmith
from src.observability.metrics import AgentMetrics
from src.observability.tracing import AgentTracer

def test_setup_logging():
    setup_logging()
    logger = get_logger("test")
    assert logger is not None

def test_agent_metrics():
    metrics = AgentMetrics()
    assert metrics.total_requests == 0
    metrics.increment_request()
    assert metrics.total_requests == 1

def test_agent_tracer():
    trace_id = AgentTracer.start_trace()
    assert len(trace_id) == 8

"""业务指标采集"""
from dataclasses import dataclass, field
from collections import defaultdict
import threading

@dataclass
class AgentMetrics:
    """Agent 运行指标"""
    total_requests: int = 0
    total_tool_calls: int = 0
    agent_route_counts: dict = field(default_factory=lambda: defaultdict(int))
    total_response_time_ms: float = 0.0
    error_count: int = 0
    pii_redaction_count: int = 0
    human_approval_count: int = 0
    human_rejection_count: int = 0
    model_fallback_count: int = 0
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    @property
    def avg_response_time_ms(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.total_response_time_ms / self.total_requests

    def increment_request(self):
        with self._lock:
            self.total_requests += 1

    def increment_tool_call(self):
        with self._lock:
            self.total_tool_calls += 1

    def increment_error(self):
        with self._lock:
            self.error_count += 1

    def record_route(self, agent_name: str):
        with self._lock:
            self.agent_route_counts[agent_name] += 1

    def record_response_time(self, ms: float):
        with self._lock:
            self.total_response_time_ms += ms

    def to_dict(self) -> dict:
        with self._lock:
            return {
                "total_requests": self.total_requests,
                "total_tool_calls": self.total_tool_calls,
                "agent_route_counts": dict(self.agent_route_counts),
                "avg_response_time_ms": round(self.avg_response_time_ms, 2),
                "error_count": self.error_count,
                "pii_redaction_count": self.pii_redaction_count,
                "human_approval_count": self.human_approval_count,
                "human_rejection_count": self.human_rejection_count,
                "model_fallback_count": self.model_fallback_count,
            }

_global_metrics = AgentMetrics()

def get_metrics() -> AgentMetrics:
    return _global_metrics

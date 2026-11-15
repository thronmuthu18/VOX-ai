"""
MuthuAI Phase 6 — monitoring/metrics.py

Performance Metrics & Execution Telemetry.
Tracks tool execution counts, execution latencies, and success/failure rates.
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from utils.logger import get_logger

log = get_logger("muthuai.monitoring.metrics")


@dataclass
class MetricRecord:
    tool_name: str
    duration_ms: float
    success: bool
    timestamp: float = field(default_factory=time.time)


class MetricsCollector:
    """
    Collects performance telemetry and tool execution metrics.
    """

    _instance: "MetricsCollector" | None = None

    def __init__(self) -> None:
        self._records: list[MetricRecord] = []

    @classmethod
    def get_instance(cls) -> "MetricsCollector":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def record_execution(self, tool_name: str, duration_ms: float, success: bool) -> None:
        rec = MetricRecord(tool_name=tool_name, duration_ms=round(duration_ms, 2), success=success)
        self._records.append(rec)
        log.debug("Metric: %s took %.1fms (success=%s)", tool_name, duration_ms, success)

    def summary(self) -> dict:
        total = len(self._records)
        if total == 0:
            return {"total_executions": 0, "success_rate": 1.0, "avg_latency_ms": 0.0}

        successes = sum(1 for r in self._records if r.success)
        avg_lat = sum(r.duration_ms for r in self._records) / total

        return {
            "total_executions": total,
            "successes": successes,
            "failures": total - successes,
            "success_rate": round(successes / total, 3),
            "avg_latency_ms": round(avg_lat, 2)
        }

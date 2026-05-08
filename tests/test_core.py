import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest

from health_probe import (
    HealthProbeError,
    HealthRegistry,
    HealthStatus,
    UnknownCheckError,
)


class FakeClock:
    def __init__(self, tick_ms: float = 10.0) -> None:
        self.now = 100.0
        self.tick = tick_ms / 1000.0

    def __call__(self) -> float:
        self.now += self.tick
        return self.now


def test_healthy_check_passes():
    registry = HealthRegistry(clock=FakeClock())
    registry.register("db", lambda: True)
    result = registry.run_check("db")
    assert result.passed
    assert result.status is HealthStatus.HEALTHY


def test_false_check_unhealthy():
    registry = HealthRegistry(clock=FakeClock())
    registry.register("cache", lambda: False)
    result = registry.run_check("cache")
    assert not result.passed
    assert result.status is HealthStatus.UNHEALTHY


def test_string_result_means_degraded():
    registry = HealthRegistry(clock=FakeClock())
    registry.register("queue", lambda: "backlog growing")
    result = registry.run_check("queue")
    assert result.passed
    assert result.status is HealthStatus.DEGRADED
    assert result.detail == "backlog growing"


def test_exception_captured_not_raised():
    def broken():
        raise ConnectionError("socket closed")

    registry = HealthRegistry(clock=FakeClock())
    registry.register("api", broken)
    result = registry.run_check("api")
    assert not result.passed
    assert "ConnectionError" in result.detail


def test_unknown_check_raises():
    with pytest.raises(UnknownCheckError):
        HealthRegistry().run_check("phantom")


def test_slow_check_flags_degraded():
    slow_clock = FakeClock(tick_ms=2500)
    registry = HealthRegistry(clock=slow_clock)
    registry.register("disk", lambda: True, warn_threshold_ms=2000)
    result = registry.run_check("disk")
    assert result.status is HealthStatus.DEGRADED
    assert "slow" in result.detail


def test_overall_status_worst_wins():
    registry = HealthRegistry(clock=FakeClock())
    registry.register("ok", lambda: True)
    registry.register("bad", lambda: False)
    report = registry.run_all()
    assert report.overall is HealthStatus.UNHEALTHY
    assert report.failing_checks == ("bad",)


def test_degraded_overall():
    registry = HealthRegistry(clock=FakeClock())

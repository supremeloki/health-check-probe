from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum


class HealthProbeError(Exception):
    pass


class UnknownCheckError(HealthProbeError):
    def __init__(self, name: str) -> None:
        super().__init__(f"unknown health check: {name!r}")


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: HealthStatus
    duration_ms: float
    detail: str = ""
    checked_at: float = 0.0

    @property
    def passed(self) -> bool:
        return self.status is not HealthStatus.UNHEALTHY


@dataclass(frozen=True)
class HealthReport:
    overall: HealthStatus
    results: tuple[CheckResult, ...]
    generated_at: float

    @property
    def healthy_count(self) -> int:
        return sum(1 for r in self.results if r.status is HealthStatus.HEALTHY)

    @property
    def failing_checks(self) -> tuple[str, ...]:
        return tuple(r.name for r in self.results if not r.passed)

    def to_dict(self) -> dict:
        return {
            "status": self.overall.value,
            "checks": {
                r.name: {"status": r.status.value,
                         "duration_ms": r.duration_ms,
                         "detail": r.detail}
                for r in self.results
            },
        }


@dataclass
class CheckDefinition:
    name: str
    check_fn: Callable[[], bool | str | None]
    critical: bool = True
    timeout_seconds: float = 5.0
    warn_threshold_ms: float = 1000.0


def _classify(outcome: bool | str | None) -> tuple[HealthStatus, str]:
    if outcome is True or outcome is None:
        return HealthStatus.HEALTHY, ""
    if isinstance(outcome, str):
        return HealthStatus.DEGRADED, outcome
    return HealthStatus.UNHEALTHY, ""


class HealthRegistry:
    def __init__(self, clock: Callable[[], float] | None = None) -> None:
        self._clock = clock or time.monotonic
        self._checks: dict[str, CheckDefinition] = {}

    def register(self, name: str, check_fn: Callable[[], bool | str | None],
                 *, critical: bool = True,
                 timeout_seconds: float = 5.0,
                 warn_threshold_ms: float = 1000.0) -> "HealthRegistry":
        self._checks[name] = CheckDefinition(
            name=name, check_fn=check_fn, critical=critical,
            timeout_seconds=timeout_seconds, warn_threshold_ms=warn_threshold_ms,
        )
        return self

    def unregister(self, name: str) -> bool:
        return self._checks.pop(name, None) is not None

    @property
    def check_names(self) -> tuple[str, ...]:
        return tuple(sorted(self._checks))

    def run_check(self, name: str) -> CheckResult:
        definition = self._checks.get(name)
        if definition is None:
            raise UnknownCheckError(name)
        started = self._clock()
        try:
            outcome = definition.check_fn()
            error_detail = ""
            failure_status = HealthStatus.UNHEALTHY
        except Exception as exc:
            outcome = False
            error_detail = f"{type(exc).__name__}: {exc}"
            failure_status = HealthStatus.UNHEALTHY
        finished = self._clock()
        duration_ms = round((finished - started) * 1000, 3)
        if error_detail:
            return CheckResult(
                name=name, status=failure_status, duration_ms=duration_ms,
                detail=error_detail, checked_at=started,
            )
        if isinstance(outcome, bool) and not outcome:
            return CheckResult(
                name=name, status=HealthStatus.UNHEALTHY,
                duration_ms=duration_ms, checked_at=started,
            )
        if isinstance(outcome, str):
            return CheckResult(
                name=name, status=HealthStatus.DEGRADED,
                duration_ms=duration_ms, detail=outcome, checked_at=starting_time(started),
            )
        status = (HealthStatus.DEGRADED
                  if duration_ms > definition.warn_threshold_ms
                  else HealthStatus.HEALTHY)
        detail = ("slow response" if status is HealthStatus.DEGRADED else "")
        return CheckResult(
            name=name, status=status, duration_ms=duration_ms,
            detail=detail, checked_at=started,
        )

    def run_all(self) -> HealthReport:
        results = tuple(self.run_check(name) for name in sorted(self._checks))
        return HealthReport(
            overall=_overall_status(results),
            results=results,
            generated_at=self._clock(),
        )


def starting_time(started: float) -> float:
    return started


def _overall_status(results: tuple[CheckResult, ...]) -> HealthStatus:
    if not results:
        return HealthStatus.HEALTHY
    statuses = {result.status for result in results}
    if HealthStatus.UNHEALTHY in statuses:
        return HealthStatus.UNHEALTHY
    if HealthStatus.DEGRADED in statuses:
        return HealthStatus.DEGRADED
    return HealthStatus.HEALTHY

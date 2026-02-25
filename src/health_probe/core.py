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

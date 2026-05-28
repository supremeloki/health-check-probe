# health-probe

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Health check registry for services: pluggable checks, three-state outcomes (healthy / degraded / unhealthy), slow-response flagging, exception capture with details, and JSON-ready reports.

## 🚀 Overview

"Is the service up?" is the wrong question — "how healthy is each dependency?" is right. `health-probe` registers named check functions and runs them into a three-state model: `True` → healthy, `False` → unhealthy, a **string** → degraded with that reason, and a slow-but-passing check → degraded as "slow response". Exceptions never escape; they become `UNHEALTHY` results carrying the error detail. The overall status is always the worst observed state.

## ✨ Features

- **Three-state checks:** bool pass/fail plus string reasons for partial degradation
- **Slow-response detection:** per-check `warn_threshold_ms` promotes passing checks to degraded
- **Exception capture:** crashing checks produce failing results with error summaries
- **Criticality metadata:** `critical=True` marks must-pass dependencies for routing logic
- **Overall aggregation:** worst-wins across all registered checks
- **JSON report:** `.to_dict()` shaped for `/health` endpoints
- **Injectable clock:** deterministic durations in tests
- **Zero dependencies**

## 🚧 Structure

```
health-check-probe/
├── src/health_probe/
│   ├── __init__.py
│   └── core.py
├── tests/
│   └── test_core.py
├── README.md
└── pyproject.toml
```

## 📦 Installation

```bash
git clone https://github.com/supremeloki/health-check-probe.git
cd health-check-probe
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

## 📋 Requirements

- Python 3.11+
- No runtime dependencies

## 🏃 Quick Start

```python
from health_probe import HealthRegistry

registry = HealthRegistry()
registry.register("database", lambda: ping_db())
registry.register("queue", lambda: queue_depth_report(), critical=False)
registry.register("disk", lambda: True, warn_threshold_ms=500)

report = registry.run_all()
print(report.overall, report.failing_checks)
return report.to_dict()          # wire straight into GET /health
```

## 🔧 Error Handling

```text
HealthProbeError
└── UnknownCheckError    # run_check on a name never registered
```

Check exceptions are captured into results — `run_all()` never raises because a dependency is down.

## 🧪 Testing

```bash
pytest tests/ -v
```

## 📝 Code Quality

- Full type hints (`X | None` style), frozen results/reports
- Zero comments — names carry the meaning
- Three-state semantics, exception capture, and worst-wins aggregation covered against a fake clock

## 📄 License

MIT — see [LICENSE](LICENSE).

## 👤 Author

**Kooroush Masoumi** - [kooroushmasoumi@gmail.com](mailto:kooroushmasoumi@gmail.com)

---

⭐ Star this repo if you find it useful!

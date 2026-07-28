"""Emits a machine-readable record of every test run.

The output feeds the public /tests page, which needs more than pass/fail: it
shows what each test actually asserts. That description comes from the test's
own docstring, so the page can never drift from the suite — a test with no
docstring shows no claim rather than an invented one.

Written to backend/test-report.json on every run. The merge script in
frontend/scripts folds it together with the Vitest and Playwright reports.

Wired up from conftest.py, which owns the pytest hooks.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

REPORT_PATH = Path(__file__).parent.parent / "test-report.json"

# Mirrors TEST_CATEGORIES in conftest.py — the directory a test lives in.
KNOWN_CATEGORIES = (
    "unit",
    "integration",
    "performance",
    "security",
    "multilingual",
    "resilience",
    "contract",
)


def humanise(node_name: str) -> str:
    """`test_cache_hit_skips_chroma[hi]` -> `Cache hit skips chroma [hi]`."""
    name, params = node_name, ""
    if "[" in name:
        name, _, rest = name.partition("[")
        params = " [" + rest
    name = name.removeprefix("test_").replace("_", " ").strip()
    if not name:
        return node_name
    return name[:1].upper() + name[1:] + params


class TestReportCollector:
    """Collects one record per test and writes them all out at session end."""

    def __init__(self) -> None:
        self._records: dict[str, dict] = {}
        self._started = time.time()

    def record(self, report) -> None:
        # Each test produces setup/call/teardown reports. The call phase is the
        # test body; a failure during setup or teardown must still be recorded,
        # otherwise a broken fixture shows up as a silently missing test.
        if report.when == "call":
            outcome = "skipped" if report.skipped else report.outcome
        elif report.outcome == "failed":
            outcome = "error"
        else:
            return

        # Never let a later passing phase overwrite an earlier failure.
        existing = self._records.get(report.nodeid)
        if existing and existing["outcome"] in {"failed", "error"}:
            return

        path, _, node_name = report.nodeid.partition("::")
        parts = Path(path).parts
        category = next((p for p in parts if p in KNOWN_CATEGORIES), "unit")
        segments = node_name.split("::")

        self._records[report.nodeid] = {
            "id": report.nodeid,
            "suite": "backend",
            "category": category,
            "file": path,
            "group": segments[0] if len(segments) > 1 else "",
            "name": humanise(segments[-1]),
            "purpose": getattr(report, "voicecare_docstring", ""),
            "outcome": outcome,
            "duration_ms": round(report.duration * 1000, 2),
        }

    def write(self) -> dict:
        records = sorted(
            self._records.values(),
            key=lambda r: (r["category"], r["file"], r["name"]),
        )
        payload = {
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "suite": "backend",
            "duration_ms": round((time.time() - self._started) * 1000, 2),
            "total": len(records),
            "passed": sum(1 for r in records if r["outcome"] == "passed"),
            "failed": sum(1 for r in records if r["outcome"] in {"failed", "error"}),
            "skipped": sum(1 for r in records if r["outcome"] == "skipped"),
            "tests": records,
        }
        REPORT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return payload

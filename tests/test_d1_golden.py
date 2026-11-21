import json
import os
from pathlib import Path

import pytest

from mutant_forge.runner import consistent, repeat

pytestmark = [pytest.mark.moose, pytest.mark.bench]


def test_d1_reproduces_on_the_pinned_build():
    case = Path(os.environ["MF_BENCH_DIR"]) / "benchmark/public/cases/D1-SOLVER-DTMIN-001"
    expected = json.loads((case / "evidence/solver-events.json").read_text(encoding="utf-8"))
    runs = repeat(Path(os.environ["MF_MOOSE_EXE"]), case / "artifacts/failing.i")
    assert [r.exit_code for r in runs] == [1, 1, 1]
    assert consistent(runs)
    assert all(r.unclassified == [] for r in runs)
    assert runs[0].events == [e["message"] for e in expected["ordered_events"]]

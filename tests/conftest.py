import os
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"

# The 11 solver messages in fixtures/d1_like.log, in order.
D1_EVENTS = [
    "Time Step 1, time = 2, dt = 2",
    "Linear solve did not converge due to DIVERGED_ITS iterations 0",
    "Nonlinear solve did not converge due to DIVERGED_LINE_SEARCH iterations 0",
    "Solve Did NOT Converge!",
    "Aborting as solve did not converge",
    "Time Step 1, time = 1, dt = 1",
    "Linear solve did not converge due to DIVERGED_ITS iterations 0",
    "Nonlinear solve did not converge due to DIVERGED_LINE_SEARCH iterations 0",
    "Solve Did NOT Converge!",
    "Aborting as solve did not converge",
    "Solve failed and timestep already at or below dtmin, cannot continue!",
]

# Each marker names the environment variable it needs; the test skips when it is missing.
NEEDS = {"moose": "MF_MOOSE_EXE", "bench": "MF_BENCH_DIR", "api": "ANTHROPIC_API_KEY"}


def read(name: str) -> str:
    # read_bytes keeps "\r\n"; read_text would turn it into "\n" and hide the CRLF case
    return (FIXTURES / name).read_bytes().decode("utf-8")


def pytest_collection_modifyitems(config, items):
    for item in items:
        for marker, var in NEEDS.items():
            if item.get_closest_marker(marker) and not os.environ.get(var):
                item.add_marker(pytest.mark.skip(reason=f"needs ${var}"))

import os
import shutil
from pathlib import Path

import pytest
from helpers import FIXTURES

# Each marker names the environment variable it needs; the test skips when it is missing.
NEEDS = {"moose": "MF_MOOSE_EXE", "bench": "MF_BENCH_DIR", "api": "ANTHROPIC_API_KEY"}


def pytest_collection_modifyitems(config, items):
    for item in items:
        for marker, var in NEEDS.items():
            if item.get_closest_marker(marker) and not os.environ.get(var):
                item.add_marker(pytest.mark.skip(reason=f"needs ${var}"))


@pytest.fixture
def fake(tmp_path):
    """An executable fake MOOSE, with the D1-like log it prints next to it."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    exe = bin_dir / "fake_moose.py"
    shutil.copy(Path(__file__).parent / "fake_moose.py", exe)
    shutil.copy(FIXTURES / "d1_like.log", bin_dir)
    exe.chmod(0o755)
    return exe


@pytest.fixture
def inp(tmp_path):
    """Returns a function that writes a small input for the fake MOOSE."""

    def write(mode: str, dt: str = "2") -> Path:
        f = tmp_path / f"{mode}-{dt}.i"
        counter = tmp_path / "flaky.count"
        f.write_text(f"# FAKE: mode={mode}\n# FAKE: counter={counter}\ndt = {dt}\ndtmin = 1\n")
        return f

    return write

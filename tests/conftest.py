import os

import pytest

# Each marker names the environment variable it needs; the test skips when it is missing.
NEEDS = {"moose": "MF_MOOSE_EXE", "bench": "MF_BENCH_DIR", "api": "ANTHROPIC_API_KEY"}


def pytest_collection_modifyitems(config, items):
    for item in items:
        for marker, var in NEEDS.items():
            if item.get_closest_marker(marker) and not os.environ.get(var):
                item.add_marker(pytest.mark.skip(reason=f"needs ${var}"))

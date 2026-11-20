import os
import re
from pathlib import Path

import pytest

from mutant_forge.hitedit import set_param
from mutant_forge.runner import check_input, run_moose

pytestmark = pytest.mark.moose

BASES = Path(__file__).parents[1] / "bases"
NONLINEAR = ["nlheat1dt.i", "nlheat2dt.i"]
NEWTON_LINE = re.compile(r"^\s*\d+ Nonlinear \|R\|", re.M)


def exe() -> Path:
    return Path(os.environ["MF_MOOSE_EXE"])


@pytest.mark.parametrize("name", ["diff1dt.i", "diff2ds.i", *NONLINEAR])
def test_base_runs_clean(name):
    assert check_input(exe(), BASES / name).exit_code == 0
    r = run_moose(exe(), BASES / name)
    assert r.exit_code == 0 and r.seconds < 10 and r.unclassified == []
    assert all(e.startswith("Time Step") for e in r.events)


# F2 allows one Newton iteration, so it can only fail where a clean step needs two or more
@pytest.mark.parametrize("dt", [None, "1", "32"])
@pytest.mark.parametrize("name", NONLINEAR)
def test_nonlinear_base_needs_two_newton_steps(name, dt, tmp_path):
    f = BASES / name
    if dt:
        f = tmp_path / name
        f.write_text(set_param((BASES / name).read_text(), "Executioner/dt", dt))
    r = run_moose(exe(), f)
    assert r.exit_code == 0 and r.unclassified == []
    assert len(NEWTON_LINE.findall(r.output)) >= 3

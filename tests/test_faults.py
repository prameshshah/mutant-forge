from collections import Counter
from pathlib import Path

import pytest

from mutant_forge.faults import BASE_KINDS, FaultNotApplicable, FaultSpec, apply_fault, load_plan
from mutant_forge.hitedit import changed_paths, params

ROOT = Path(__file__).parents[1]
PLAN = load_plan(ROOT / "configs" / "run-v0.yaml")


def base(name: str) -> str:
    return (ROOT / "bases" / f"{name}.i").read_text(encoding="utf-8")


def test_f1_edits():
    spec = FaultSpec("s1", "diff1dt", "F1", {"dt": "2", "dtmin": "1"})
    out = apply_fault(base("diff1dt"), BASE_KINDS["diff1dt"], spec)
    assert changed_paths(base("diff1dt"), out) == {
        "Executioner/dt",
        "Executioner/dtmin",
        "Executioner/petsc_options_iname",
        "Executioner/petsc_options_value",
    }


def test_f2_needs_nonlinear():
    spec = FaultSpec("s2", "diff1dt", "F2", {"dt": "2", "dtmin": "1"})
    with pytest.raises(FaultNotApplicable):
        apply_fault(base("diff1dt"), BASE_KINDS["diff1dt"], spec)


def test_f4_needs_steady():
    spec = FaultSpec("s3", "diff1dt", "F4", {"nx": "10", "ny": "10"})
    with pytest.raises(FaultNotApplicable):
        apply_fault(base("diff1dt"), BASE_KINDS["diff1dt"], spec)


def test_f4_removes_all_bcs_and_keeps_the_source():
    spec = FaultSpec("s4", "diff2ds", "F4", {"nx": "10", "ny": "10"})
    out = params(apply_fault(base("diff2ds"), BASE_KINDS["diff2ds"], spec))
    assert not any(k.startswith("BCs/") for k in out)
    assert out["Kernels/source/type"] == "BodyForce"


def test_wrong_params_rejected():
    spec = FaultSpec("s5", "diff1dt", "F1", {"dt": "2"})
    with pytest.raises(ValueError, match="dtmin"):
        apply_fault(base("diff1dt"), BASE_KINDS["diff1dt"], spec)


def test_plan_has_40_unique_specs():
    assert len(PLAN) == 40 and len({s.spec_id for s in PLAN}) == 40
    assert Counter(s.fault_id for s in PLAN) == {"F1": 12, "F2": 8, "F3": 12, "F4": 8}


def test_shallow_deep_pairs_first():
    for key in {(s.base, s.fault_id) for s in PLAN if s.fault_id != "F4"}:
        first_two = [s.params["dt"] for s in PLAN if (s.base, s.fault_id) == key][:2]
        assert first_two == ["2", "32"], key


def test_f3_allows_more_than_a_clean_step():
    # a clean step needs 8 or 9 Newton iterations; a lower cap repeats F2's failure
    assert all(int(s.params["nl_max_its"]) >= 15 for s in PLAN if s.fault_id == "F3")


def test_f4_specs_differ():
    f4 = [s for s in PLAN if s.fault_id == "F4"]
    assert len({(s.params["nx"], s.params["ny"]) for s in f4}) == len(f4)


def test_every_spec_applies():
    for s in PLAN:
        out = apply_fault(base(s.base), BASE_KINDS[s.base], s)
        assert changed_paths(base(s.base), out), s.spec_id
        if "dt" in s.params:
            assert float(s.params["dtmin"]) < float(s.params["dt"]), s.spec_id

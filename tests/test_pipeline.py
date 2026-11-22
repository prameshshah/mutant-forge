import itertools
import json

import pytest
import yaml

from mutant_forge import bench
from mutant_forge.bench import SelfCheck
from mutant_forge.faults import FaultSpec
from mutant_forge.pipeline import Config, Reason, Seen, generate_one, run_all
from mutant_forge.writer import case_id_for


@pytest.fixture(autouse=True)
def offline_bench(request, monkeypatch):
    """Stand in for the benchmark CLI, except in tests marked bench."""
    if request.node.get_closest_marker("bench") is None:
        monkeypatch.setattr(bench, "validate", lambda manifest: None)
        monkeypatch.setattr(bench, "self_check", lambda *a: SelfCheck(100.0, True, False))


@pytest.fixture
def cfg(fake, tmp_path):
    return Config(
        exe=fake,
        executable="combined-opt",
        bases_dir=tmp_path / "bases",
        moose_revision="c2dfd9fedd3193740a5278ec32269450c618e3b7",
        petsc_version="3.25.2",
        base_kinds={},
        timeout_s=2,
    )


@pytest.fixture
def spec_for(cfg, tmp_path):
    """Returns a function that writes a fake base and an F1 spec that points at it."""
    ids = itertools.count()

    def make(mode: str, dt: str = "2", n: int = 0, base_mode: str | None = None) -> FaultSpec:
        name = f"{mode}{n}"
        lines = [f"# FAKE: mode={mode}", f"# FAKE: counter={tmp_path / name}.count"]
        if base_mode:
            lines.append(f"# FAKE: base={base_mode}")
        lines += ["[Executioner]", "  type = Transient", "  dt = 1", "[]", ""]
        cfg.bases_dir.mkdir(exist_ok=True)
        (cfg.bases_dir / f"{name}.i").write_text("\n".join(lines))
        cfg.base_kinds[name] = {"transient"}
        return FaultSpec(f"s{next(ids)}", name, "F1", {"dt": dt, "dtmin": "1"})

    return make


@pytest.mark.parametrize(
    "mode, reason",
    [
        ("clean", "no_failure"),
        ("flaky", "nondeterministic"),
        ("crash", "crash"),
        ("hang", "timeout"),
        ("unknown", "unclassified_message"),
        ("badparse", "parse_failed"),
        ("nonlinear", "wrong_cause"),
    ],
)
def test_rejections(spec_for, cfg, tmp_path, mode, reason):
    o = generate_one(spec_for(mode), cfg, tmp_path / "out", Seen())
    assert (o.status, o.reason) == ("rejected", reason)


def test_kept_d1_like(spec_for, cfg, tmp_path):
    root = tmp_path / "out"
    o = generate_one(spec_for("d1"), cfg, root, Seen())
    assert o.status == "kept" and o.reason is None
    assert (o.failure_stage, o.terminal_symptom) == ("linear_solve", "timestep_at_or_below_dtmin")
    case = yaml.safe_load((root / "public/cases" / o.case_id / "case.yaml").read_text())
    assert case["title"].startswith("Draft (generated):")


def test_base_not_clean(spec_for, cfg, tmp_path):
    o = generate_one(spec_for("d1", base_mode="d1"), cfg, tmp_path / "out", Seen())
    assert o.reason == "base_not_clean"


def test_unclassified_in_any_run_rejects(spec_for, cfg, tmp_path):
    o = generate_one(spec_for("unknown_once"), cfg, tmp_path / "out", Seen())
    assert o.reason == "unclassified_message"


def test_identical_events_are_duplicate(spec_for, cfg, tmp_path):
    seen = Seen()
    outs = [generate_one(spec_for("d1"), cfg, tmp_path / "out", seen) for _ in range(2)]
    assert [o.reason for o in outs] == [None, "duplicate"]


def test_same_events_on_another_base_is_duplicate(spec_for, cfg, tmp_path):
    seen = Seen()
    outs = [generate_one(spec_for("d1", n=n), cfg, tmp_path / "out", seen) for n in (0, 1)]
    assert outs[0].base != outs[1].base
    assert [o.reason for o in outs] == [None, "duplicate"]


def test_family_cap(spec_for, cfg, tmp_path):
    seen = Seen()
    outs = [generate_one(spec_for("d1", dt=dt), cfg, tmp_path / "out", seen) for dt in "234"]
    assert [o.reason for o in outs] == [None, None, "duplicate"]


def test_self_check_failure_is_rejected(spec_for, cfg, tmp_path, monkeypatch):
    monkeypatch.setattr(bench, "self_check", lambda *a: SelfCheck(65.0, False, False))
    root = tmp_path / "out"
    o = generate_one(spec_for("d1"), cfg, root, Seen())
    assert o.reason == "self_check_failed"
    assert not (root / "public/cases" / case_id_for("d10", "F1", 1)).exists()
    assert yaml.safe_load((root / "manifest.yaml").read_text())["cases"] == []


def test_every_spec_accounted(spec_for, cfg, tmp_path):
    modes = ["clean", "d1", "crash", "unknown", "badparse", "nonlinear", "flaky"]
    root = tmp_path / "out"
    outcomes = run_all([spec_for(m) for m in modes], cfg, root)
    assert len(outcomes) == 7
    lines = (root / "outcomes.jsonl").read_text().splitlines()
    assert [json.loads(line)["spec_id"] for line in lines] == [o.spec_id for o in outcomes]


def test_run_all_refuses_a_used_folder(spec_for, cfg, tmp_path):
    root = tmp_path / "out"
    root.mkdir()
    (root / "old.txt").write_text("x")
    with pytest.raises(ValueError, match="not empty"):
        run_all([spec_for("d1")], cfg, root)


def test_label_errors_are_reasons():
    assert all(Reason(r) for r in ("label_unknown", "no_first_failure", "no_terminal_symptom"))


@pytest.mark.bench
def test_kept_case_passes_the_benchmark(spec_for, cfg, tmp_path):
    o = generate_one(spec_for("d1"), cfg, tmp_path / "out", Seen())
    assert o.status == "kept", o.detail

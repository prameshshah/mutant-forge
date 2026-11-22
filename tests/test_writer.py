import hashlib
import json
from dataclasses import replace
from pathlib import Path

import yaml
from helpers import d1_spec

from mutant_forge.lexicon import Lexicon
from mutant_forge.writer import case_id_for, write_case, write_manifest, wrong_stage_response

LEX = Lexicon.load()
SPEC = d1_spec()
CASE = "public/cases/D1-MF-DIFF1DT-F1-001"
PRIVATE = "private/cases/D1-MF-DIFF1DT-F1-001"


def sha(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_layout(tmp_path):
    write_case(SPEC, tmp_path, LEX)
    for p in [
        f"{CASE}/case.yaml",
        f"{CASE}/prompt.md",
        f"{CASE}/artifacts/failing.i",
        f"{CASE}/evidence/solver-events.json",
        f"{CASE}/evidence/run-metadata.json",
        f"{PRIVATE}/evaluation.yaml",
        f"{PRIVATE}/reproduction.md",
        f"{PRIVATE}/validation-summary.json",
        f"{PRIVATE}/validation/run-1.log",
        f"{PRIVATE}/validation/run-3.status",
        "example-submissions/D1-MF-DIFF1DT-F1-001/response.json",
        "example-submissions/D1-MF-DIFF1DT-F1-001-mutant-001/response.json",
    ]:
        assert (tmp_path / p).is_file(), p


def test_run_metadata_fields(tmp_path):
    write_case(SPEC, tmp_path, LEX)
    m = json.loads((tmp_path / CASE / "evidence/run-metadata.json").read_text())
    assert set(m) == {
        "schema_version",
        "case_id",
        "captured_on",
        "executable",
        "moose_revision",
        "petsc_version",
        "command",
        "process_count",
        "repetitions",
        "expected_exit_code",
        "timestep_attempts",
        "sha256",
    }
    assert m["timestep_attempts"] == [2, 1] and m["process_count"] == 1 and m["repetitions"] == 3


def test_hashes_match_files(tmp_path):
    write_case(SPEC, tmp_path, LEX)
    case_dir = tmp_path / CASE
    case = yaml.safe_load((case_dir / "case.yaml").read_text())
    assert case["prompt_sha256"] == sha(case_dir / case["prompt_path"])
    for item in case["artifacts"] + case["evidence_sources"]:
        assert item["sha256"] == sha(case_dir / item["path"]), item["id"]
    meta = json.loads((case_dir / "evidence/run-metadata.json").read_text())
    for path, digest in meta["sha256"].items():
        assert digest == sha(case_dir / path), path


def test_weights_sum_to_one(tmp_path):
    write_case(SPEC, tmp_path, LEX)
    ev = yaml.safe_load((tmp_path / PRIVATE / "evaluation.yaml").read_text())
    for block in ("capability_criteria", "evidence_criteria"):
        assert abs(sum(c["weight"] for c in ev[block]) - 1.0) < 1e-9, block


def test_prompt_lists_the_allowed_values(tmp_path):
    write_case(SPEC, tmp_path, LEX)
    prompt = (tmp_path / CASE / "prompt.md").read_text()
    assert "Allowed failure_stage values: linear_solve, nonlinear_solve, time_stepping" in prompt
    assert "{stages}" not in prompt and "{symptoms}" not in prompt


def test_wrong_stage_differs():
    assert wrong_stage_response(SPEC)["claim"]["failure_stage"] == "time_stepping"


def test_logs_hide_the_home_folder(tmp_path):
    home = str(Path.home())
    trace = f"9: {home}/projects/moose/modules/combined/combined-opt(+0x60f2)\n"
    run = replace(SPEC.runs[0], output=SPEC.runs[0].output + trace)
    write_case(replace(SPEC, runs=[run, run, run]), tmp_path, LEX)
    log = (tmp_path / PRIVATE / "validation/run-1.log").read_text()
    assert home not in log and "~/projects/moose/modules/combined/combined-opt" in log


def test_case_id():
    assert case_id_for("diff1dt", "F1", 1) == "D1-MF-DIFF1DT-F1-001"


def test_manifest(tmp_path):
    m = yaml.safe_load(write_manifest(tmp_path, ["A", "B"]).read_text())
    assert m["schema_version"] == "2.0" and m["required_atomic_subcategories"] == ["D1"]
    assert [c["case_id"] for c in m["cases"]] == ["A", "B"]
    assert m["cases"][0]["public_case"] == "public/cases/A/case.yaml"
    assert m["cases"][0]["private_evaluation"] == "private/cases/A/evaluation.yaml"

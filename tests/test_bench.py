import subprocess
from pathlib import Path

import pytest
from helpers import d1_spec

from mutant_forge import bench
from mutant_forge.bench import BenchError, SelfCheck, self_check, validate
from mutant_forge.lexicon import Lexicon
from mutant_forge.writer import write_case, write_manifest


@pytest.mark.bench
def test_benchmark_tools_accept_and_discriminate(tmp_path):
    spec = d1_spec()
    write_case(spec, tmp_path, Lexicon.load())
    manifest = write_manifest(tmp_path, [spec.case_id])
    validate(manifest)
    sc = self_check(manifest, spec.case_id, tmp_path)
    assert sc.gold_official_score == 100.0 and sc.gold_passed and not sc.wrong_passed


@pytest.mark.bench
def test_benchmark_cli_failure_surfaces(tmp_path):
    (tmp_path / "manifest.yaml").write_text("not: a manifest\n")
    with pytest.raises(BenchError, match="schema_version"):
        validate(tmp_path / "manifest.yaml")


# The tests below fake subprocess.run, so they run in CI without the benchmark checkout.


def test_missing_bench_dir(monkeypatch):
    monkeypatch.delenv("MF_BENCH_DIR", raising=False)
    with pytest.raises(BenchError, match="MF_BENCH_DIR"):
        validate(Path("manifest.yaml"))


@pytest.mark.parametrize(
    "outcome, message",
    [
        (FileNotFoundError("uv"), "cannot run uv"),
        (subprocess.TimeoutExpired("uv", bench.TIMEOUT_S), "timed out"),
        (subprocess.CompletedProcess([], 2, "", "ERROR: bad manifest"), "bad manifest"),
        (subprocess.CompletedProcess([], 2, "printed to stdout", ""), "printed to stdout"),
        (subprocess.CompletedProcess([], 3, "", ""), "exited 3"),
    ],
)
def test_cli_failures_raise_bench_error(monkeypatch, outcome, message):
    def fake_run(*args, **kwargs):
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    monkeypatch.setenv("MF_BENCH_DIR", "/nowhere")
    monkeypatch.setattr(bench.subprocess, "run", fake_run)
    with pytest.raises(BenchError, match=message):
        validate(Path("manifest.yaml"))


@pytest.mark.parametrize(
    "gold_score, gold_passed, wrong_passed, ok",
    [
        (100.0, True, False, True),
        (99.0, True, False, False),
        (100.0, False, False, False),
        (100.0, True, True, False),
    ],
)
def test_self_check_ok(gold_score, gold_passed, wrong_passed, ok):
    assert SelfCheck(gold_score, gold_passed, wrong_passed).ok is ok

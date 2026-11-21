"""Call the benchmark's own CLI (moose-benchmark) in its pinned checkout."""

import json
import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


class BenchError(Exception):
    """The benchmark CLI could not be run or rejected its input; carries its stderr."""


def _cli(*args) -> str:
    bench_dir = os.environ.get("MF_BENCH_DIR")
    if not bench_dir:
        raise BenchError("MF_BENCH_DIR is not set")
    cmd = ["uv", "run", "--project", bench_dir, "moose-benchmark", *map(str, args)]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError as e:
        raise BenchError(f"cannot run uv: {e}") from e
    if proc.returncode != 0:
        raise BenchError(proc.stderr.strip() or f"moose-benchmark exited {proc.returncode}")
    return proc.stdout


def validate(manifest: Path) -> None:
    _cli("validate", Path(manifest).resolve())


def record(
    manifest: Path,
    case_id: str,
    submission_dir: Path,
    provider: str,
    model: str,
    input_tokens: int = 0,
    output_tokens: int = 0,
    output: Path | None = None,
) -> None:
    submission_dir = Path(submission_dir).resolve()
    _cli(
        "record-submission",
        "--manifest",
        Path(manifest).resolve(),
        "--case-id",
        case_id,
        "--submission-dir",
        submission_dir,
        "--model-provider",
        provider,
        "--model",
        model,
        "--input-tokens",
        input_tokens,
        "--output-tokens",
        output_tokens,
        "--output",
        Path(output).resolve() if output else submission_dir / "run-record.json",
    )


def score(
    manifest: Path, case_id: str, submission_dir: Path, run_record: Path | None = None
) -> dict:
    args = ["--manifest", Path(manifest).resolve(), "--case-id", case_id]
    args += ["--submission-dir", Path(submission_dir).resolve()]
    if run_record:
        args += ["--run-record", Path(run_record).resolve()]
    return json.loads(_cli("score", *args))


@dataclass(frozen=True)
class SelfCheck:
    gold_official_score: float
    gold_passed: bool
    wrong_passed: bool

    @property
    def ok(self) -> bool:
        return self.gold_official_score == 100.0 and self.gold_passed and not self.wrong_passed


def self_check(manifest: Path, case_id: str, root: Path) -> SelfCheck:
    """Score the case's correct and wrong-stage example answers with the benchmark CLI."""
    results = {}
    # run records go to a temp folder, so the written case keeps no timestamps
    with tempfile.TemporaryDirectory() as tmp:
        for name, folder in (("gold", case_id), ("wrong", f"{case_id}-mutant-001")):
            submission = Path(root) / "example-submissions" / folder
            run_record = Path(tmp) / f"{name}.json"
            record(manifest, case_id, submission, "mutant-forge", name, output=run_record)
            results[name] = score(manifest, case_id, submission, run_record=run_record)
    gold, wrong = results["gold"], results["wrong"]
    return SelfCheck(gold["official_score"], gold["case_passed"], wrong["case_passed"])

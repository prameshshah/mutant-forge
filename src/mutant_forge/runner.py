"""Run MOOSE on one input, each time in a fresh temporary folder."""

import os
import shutil
import subprocess
import tempfile
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from mutant_forge.events import extract_events, unclassified_failure_lines


@dataclass(frozen=True)
class RunResult:
    exit_code: int | None  # None when timed out or killed by a signal
    signal: int | None
    timed_out: bool
    output: str  # stdout and stderr merged in order
    events: list[str]
    unclassified: list[str]
    seconds: float


def run_moose(
    exe: Path, input_file: Path, *, timeout_s: int = 60, extra_args: Sequence[str] = ()
) -> RunResult:
    with tempfile.TemporaryDirectory(prefix="mf-run-") as work:
        shutil.copy(input_file, work)
        cmd = [str(exe), "-i", input_file.name, "--color", "off", *extra_args]
        env = {**os.environ, "OMP_NUM_THREADS": "1"}
        start = time.monotonic()
        try:
            proc = subprocess.run(
                cmd,
                cwd=work,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=timeout_s,
                env=env,
            )
            raw, code, timed_out = proc.stdout, proc.returncode, False
        except subprocess.TimeoutExpired as e:
            # e.output is bytes, or None when nothing was printed yet
            raw, code, timed_out = e.output, None, True
        seconds = time.monotonic() - start

    output = (raw or b"").decode("utf-8", errors="replace")
    killed = code is not None and code < 0
    return RunResult(
        exit_code=None if killed else code,
        signal=-code if killed else None,
        timed_out=timed_out,
        output=output,
        events=extract_events(output),
        unclassified=unclassified_failure_lines(output),
        seconds=seconds,
    )


def check_input(exe: Path, input_file: Path) -> RunResult:
    return run_moose(exe, input_file, extra_args=["--check-input"])


def repeat(exe: Path, input_file: Path, n: int = 3, timeout_s: int = 60) -> list[RunResult]:
    return [run_moose(exe, input_file, timeout_s=timeout_s) for _ in range(n)]


def consistent(runs: list[RunResult]) -> bool:
    # an empty list gives an empty set, so "no runs" is never consistent
    return len({(r.exit_code, r.signal, r.timed_out, tuple(r.events)) for r in runs}) == 1

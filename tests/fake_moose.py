#!/usr/bin/env python3
"""Stand-in for combined-opt in tests. "# FAKE:" lines in the input pick what it prints."""

import os
import re
import signal
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent


def setting(text: str, key: str) -> str | None:
    m = re.search(rf"^# FAKE: {key}=(\S+)", text, re.M)
    return m.group(1) if m else None


def emit(text: str) -> None:
    # like MOOSE, the error block goes to stderr; flush first so the merged order is kept
    head, banner, tail = text.partition("*** ERROR ***")
    sys.stdout.write(head)
    sys.stdout.flush()
    sys.stderr.write(banner + tail)


def d1_output(dt: float) -> str:
    attempts = iter((dt, dt / 2))
    lines = []
    for line in (HERE / "d1_like.log").read_text().splitlines():
        if line.startswith("Time Step 1,"):
            t = f"{next(attempts):g}"
            line = f"Time Step 1, time = {t}, dt = {t}"
        lines.append(line)
    return "\n".join(lines) + "\n"


def nonlinear_output(dt: float) -> str:
    return (
        f"Time Step 1, time = {dt:g}, dt = {dt:g}\n"
        " 0 Nonlinear |R| = 1.000000e+00\n"
        "  Nonlinear solve did not converge due to DIVERGED_MAX_IT iterations 1\n"
        " Solve Did NOT Converge!\n"
        "Aborting as solve did not converge\n\n"
        "*** ERROR ***\n"
        "Solve failed and timestep already at or below dtmin, cannot continue!\n"
    )


def main() -> int:
    args = sys.argv[1:]
    text = Path(args[args.index("-i") + 1]).read_text()
    faulted = re.search(r"^\s*dtmin\s*=", text, re.M)
    mode = setting(text, "base") or (setting(text, "mode") if faulted else None) or "clean"
    m = re.search(r"^\s*dt\s*=\s*(\S+)", text, re.M)
    dt = float(m.group(1)) if m else 1.0
    Path("out.e").write_text("fake output\n")  # the runner must throw this folder away

    if "--check-input" in args:
        return 1 if mode == "badparse" else 0
    if mode == "clean":
        emit(f"Time Step 1, time = {dt:g}, dt = {dt:g}\n Solve Converged!\n")
        return 0
    if mode == "d1":
        emit(d1_output(dt))
        return 1
    if mode == "nonlinear":
        emit(nonlinear_output(dt))
        return 1
    if mode == "unknown":
        emit(f"Time Step 1, time = {dt:g}, dt = {dt:g}\n")
        emit("[0]PETSC ERROR: Zero pivot in LU factorization\n")
        return 1
    if mode == "flaky":
        counter = Path(setting(text, "counter"))  # outside the run folder, so it survives
        n = int(counter.read_text()) if counter.exists() else 0
        counter.write_text(str(n + 1))
        emit(d1_output(dt) if n % 2 == 0 else nonlinear_output(dt))
        return 1
    if mode == "crash":
        os.kill(os.getpid(), signal.SIGSEGV)
    if mode == "hang":
        print(f"Time Step 1, time = {dt:g}, dt = {dt:g}", flush=True)
        time.sleep(999)
    if mode == "badparse":
        emit("*** ERROR ***\ninput.i:3: syntax error\n")
        return 1
    sys.exit(f"fake_moose: unknown mode {mode}")


if __name__ == "__main__":
    sys.exit(main())

# Event rule

How a MOOSE log becomes the ordered message list (`solver-events.json`) that a D1-format case supplies as evidence. The benchmark's public code (`src/`, `ci/`, `tests/`, `templates/`) contains no code that writes `solver-events.json`, so this rule is this project's own. It is checked against the benchmark's public D1 case below.

## The rule

1. **Normalize** each line: remove ANSI color codes, drop `\r`, and collapse indentation and repeated spaces (`normalize_line` in `src/mutant_forge/events.py`).
2. **Keep**, in order, every normalized line that fully matches one of six patterns (`KEEP_PATTERNS`):

   ```
   ^Time Step \d+, time = \S+, dt = \S+$
   ^Linear solve did not converge due to \w+ iterations \d+$
   ^Nonlinear solve did not converge due to \w+ iterations \d+$
   ^Solve Did NOT Converge!$
   ^Aborting as solve did not converge$
   ^Solve failed and timestep already at or below dtmin, cannot continue!$
   ```

3. **Flag** every other line that looks like a failure (`unclassified_failure_lines`): it contains `error`, `diverged`, `did not converge`, `failed`, `nan` as a word, `zero pivot` or `segmentation`, ignoring case. The exact line `*** ERROR ***` is skipped, and scanning stops at the dtmin line, because the stack trace printed after a `mooseError` always contains "error". A run with a flagged line is rejected, never labeled.

Where each kept message comes from is listed in `docs/lexicon.md`.

## Check against the benchmark's D1 case (C1)

Run on 2026-11-20 with MOOSE `c2dfd9fedd3193740a5278ec32269450c618e3b7`, PETSc 3.25.2, `combined-opt`, one process.

- `benchmark/public/cases/D1-SOLVER-DTMIN-001/artifacts/failing.i`, run three times through `run_moose`: exit code 1 each time, identical events, no flagged lines, and the events equal the 11 `message` values of the case's `solver-events.json`, in order. `tests/test_d1_golden.py` repeats this check.
- **Output options (issue #16).** The result is identical when `-ksp_converged_reason` is removed from the input and when `-snes_converged_reason` is added (three runs each). MOOSE turns both reason options on as `::failed` unless the input sets them (`framework/src/utils/PetscSupport.C:832-845`), so PETSc prints a reason line whenever a solve fails.

## Facts the rule relies on

- MOOSE prints the error block (banner, dtmin line, stack trace, `MPI_Abort` line) to stderr, so the runner merges stderr into stdout in order.
- MOOSE prints color codes even when output goes to a file. The runner passes `--color off`, and normalization removes any that remain.
- `Time Step 0, time = 0` is printed before the first step. It has no `dt`, so it is not an event.

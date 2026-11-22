# Mutant Forge

**Breaks working simulations on purpose to make draft test questions for AI debugging assistants.**

When a simulation fails, the last error message is the loudest, but the real cause usually happened earlier. Mutant Forge makes test cases that check whether an AI can find that real cause.

## How it works

```
working MOOSE input -> break it in one known way -> run it 3 times -> keep what it prints
                    -> write a test case with the right answer -> check it with the benchmark's own grader
```

Because the input was broken on purpose, we know where it should fail first, and every run is checked to make sure it really failed there.

## What it made (v0)

- **40** attempts, **14** draft test cases kept
- **26** dropped as duplicates: 13 had the same messages as a kept case, and 13 came after their problem and fault already had 2 cases
- **0** dropped for any other reason
- Every kept case gave the same result in 3 runs, passes the benchmark's checker, and its right answer scores 100 while a wrong answer fails
- Running all 40 again gives the same 14

The cases are in `drafts/`. `drafts/outcomes.jsonl` says what happened to each of the 40 attempts.

## The four ways it breaks things

| Fault | What it changes | Where it fails first |
|---|---|---|
| F1 | the linear solver gets 0 iterations | linear solver |
| F2 | the nonlinear solver gets 1 iteration | nonlinear solver |
| F3 | asks for accuracy that cannot be reached | nonlinear solver |
| F4 | removes the boundary conditions | linear solver |

## Why the answers can be trusted

- The fault is put in on purpose, so we know where the run should fail first. A run that fails somewhere else is dropped.
- Every message is traced to the MOOSE source line, or the PETSc option, that prints it (`docs/lexicon.md`).
- On the benchmark's own sample case, this setup reproduces its 11 recorded messages exactly (`tests/test_d1_golden.py`).
- If a run prints anything unexpected, the case is dropped, never guessed.

## Format

The cases use the D1 format of [moose-agent-benchmark](https://github.com/MengnanLi91/moose-agent-benchmark) (schema 2.0): read the input and its solver messages, then name **where it first failed** and **how it ended**. They are draft cases for review, not part of that benchmark.

The benchmark is only read: its public sample case, its code and its checker. Nothing from its private or example-answer folders is used. The grading files and example answers for these drafts are public here, in `drafts/`, so they can be reviewed.

## Limits

- The 40 attempts were chosen after small trial runs, so 14 of 40 comes from a hand-picked list. The trials dropped settings that did not fail (F3 at a tolerance of `1e-14`, F4 without its source term) or ran too slowly (F4 on a 20x20 mesh).
- A simple rule solves these cases: the first error line is the cause, the last line is the ending. What they test is whether an AI is fooled by the louder last error.
- Labels such as `solve_aborted` are this project's own draft names.
- Tested on one MOOSE build (commit `c2dfd9fe`, PETSc 3.25.2) on one machine.

## Try it

You need MOOSE built at commit `c2dfd9fedd3193740a5278ec32269450c618e3b7`, moose-agent-benchmark checked out at `5bf036c`, and [uv](https://docs.astral.sh/uv/). Setup notes: `docs/environment.md`.

```bash
export MF_MOOSE_DIR=$HOME/projects/moose
export MF_MOOSE_EXE=$MF_MOOSE_DIR/modules/combined/combined-opt
export MF_BENCH_DIR=$HOME/projects/moose-agent-benchmark
export MF_PETSC_VERSION=3.25.2

uv sync
uv run pytest
uv run mutant-forge generate --spec-id f1-diff1dt-1 --plan configs/run-v0.yaml --out out/one   # one case, about 10 s
uv run mutant-forge run-all --plan configs/run-v0.yaml --out out/run                          # all 40, about 3 min
uv run --project $MF_BENCH_DIR moose-benchmark validate drafts/manifest.yaml
```

Without the four variables, `uv run pytest` skips the tests that need MOOSE or the benchmark.

## What's inside

```
bases/     four working problems that get broken
configs/   the 40 attempts
src/       the code
tests/     tests on a fake MOOSE, and tests on the real build
drafts/    the 14 kept cases and the results of all 40 attempts
docs/      setup, how messages are read, what each message means
```

MIT license.

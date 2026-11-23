# Probe: MOOSE's own tutorial inputs

A first check of whether the faults also work on MOOSE's own tutorial problems, not only on this project's `bases/`. This is a probe: no cases were written from these runs, and nothing here is part of `drafts/`.

Run on 2026-11-23 with MOOSE `c2dfd9fedd3193740a5278ec32269450c618e3b7`, PETSc 3.25.2, `combined-opt`, one process. The inputs were read from the MOOSE checkout and are not copied into this repository.

## The two inputs, run unchanged

| Input (path in the MOOSE repository) | Exit code | Time steps | `Nonlinear \|R\|` lines per step | Unknown lines |
|---|---|---|---|---|
| `modules/heat_transfer/tutorials/introduction/therm_step03.i` | 0 | 5 | 3 | 0 |
| `tutorials/darcy_thermo_mech/step05_heat_conduction/problems/step5b_transient.i` | 0 | 10 | 3 | 0 |

Three residual lines per step means each clean step needs two Newton iterations, so F2 (one iteration allowed) has room to fail.

## The same inputs with a fault

Every faulted input used `dt = 2` and `dtmin = 1`. F3 also set `nl_rel_tol = 1e-20`, `nl_abs_tol = 1e-50` and `nl_max_its = 20`. Each faulted input ran three times through `run_moose`.

| Input | Fault | Exit codes | Same events in all three runs | Unknown lines | First failure | Labels |
|---|---|---|---|---|---|---|
| `therm_step03.i` | F1 | 1, 1, 1 | yes | 0 | `Linear solve did not converge due to DIVERGED_ITS iterations 0` | `linear_solve`, `timestep_at_or_below_dtmin` |
| `therm_step03.i` | F2 | 1, 1, 1 | yes | 0 | `Nonlinear solve did not converge due to DIVERGED_MAX_IT iterations 1` | `nonlinear_solve`, `timestep_at_or_below_dtmin` |
| `therm_step03.i` | F3 | 1, 1, 1 | yes | 0 | `Nonlinear solve did not converge due to DIVERGED_MAX_IT iterations 20` | `nonlinear_solve`, `timestep_at_or_below_dtmin` |
| `step5b_transient.i` | F1 | 1, 1, 1 | yes | 0 | `Linear solve did not converge due to DIVERGED_ITS iterations 0` | `linear_solve`, `timestep_at_or_below_dtmin` |
| `step5b_transient.i` | F2 | 1, 1, 1 | yes | 0 | `Nonlinear solve did not converge due to DIVERGED_MAX_IT iterations 1` | `nonlinear_solve`, `timestep_at_or_below_dtmin` |
| `step5b_transient.i` | F3 | 1, 1, 1 | yes | 0 | `Nonlinear solve did not converge due to DIVERGED_LINE_SEARCH iterations 7` | `nonlinear_solve`, `timestep_at_or_below_dtmin` |

## What this shows, and what it does not

- It shows that on these two tutorial inputs, F1 to F3 fail at the intended stage, repeatably, and print only messages the lexicon already knows.
- It does not show that these runs would become kept cases. They did not go through the pipeline, so there was no duplicate check and no benchmark self-check.
- It says nothing yet about other tutorials or modules.
- F3 on `therm_step03.i` stopped at its 20-iteration cap instead of a line-search failure. Some F3 runs on this project's own bases do the same.

## Which MOOSE inputs the editor can read

Checked on 2026-11-22: `hitedit` reads 5 of 5 inputs in the heat transfer tutorial, 72 of 73 in the Darcy thermo-mechanics tutorial, and 4 of 31 in `examples/`, where most files use the older `[./name]` block style it does not support yet. Some Darcy tutorial inputs (step 5c, steps 6a to 6c) exit with code 1 while loading on `combined-opt`. That was not investigated; they may need the tutorial's own application.

# Message lexicon

`src/mutant_forge/lexicon.yaml` names every solver message the pipeline recognizes. A run is labeled from it:

- **failure stage**: the stage of the first line whose role is `failure`
- **terminal symptom**: the label of the last line, which must be a `terminal` row

| Message pattern | Printed by | Component | Role | Label |
|---|---|---|---|---|
| `Time Step <n>, time = <t>, dt = <dt>` | issue #8 | time_stepper | context | - |
| `Linear solve did not converge due to <REASON> iterations <n>` | issue #8 | linear_solver | failure | `linear_solve` |
| `Nonlinear solve did not converge due to <REASON> iterations <n>` | issue #8 | nonlinear_solver | failure | `nonlinear_solve` |
| `Solve Did NOT Converge!` | issue #8 | time_stepper | downstream | - |
| `Aborting as solve did not converge` | issue #8 | time_stepper | downstream | - |
| `Solve failed and timestep already at or below dtmin, cannot continue!` | issue #8 | time_stepper | terminal | `timestep_at_or_below_dtmin` |

## Columns

- **Message pattern**: the line after indentation and color codes are removed. The exact regex is in `lexicon.yaml` and must match the extractor's patterns in `events.py` (a test checks this).
- **Printed by**: the file and line at MOOSE commit `c2dfd9fe` that prints the message, or the PETSc manual page for lines PETSc prints. Filled in after the real-run check (issue #8).
- **Component**: the part of the solver the message belongs to.
- **Role**: `context` marks an attempt, `failure` is a cause, `downstream` is a consequence of an earlier failure, `terminal` is the last line, where the run gives up.
- **Label**: the identifier a correct answer uses.

`time_stepping` is the third possible failure stage. No row here makes it a first failure, so it serves as the plausible wrong answer when checking that scoring tells a right answer from a wrong one.

## Adding a row

Add a row only for a message seen in real output, and note the run that showed it. A run with a failure-looking line that matches no row is rejected, never labeled by guesswork.

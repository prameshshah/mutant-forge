# Message lexicon

`src/mutant_forge/lexicon.yaml` names every solver message the pipeline recognizes. A run is labeled from it:

- **failure stage**: the stage of the first line whose role is `failure`
- **terminal symptom**: the label of the last line, which must be a `terminal` row

| Message pattern | Printed by | Component | Role | Label |
|---|---|---|---|---|
| `Time Step <n>, time = <t>, dt = <dt>` | MOOSE `framework/src/outputs/Console.C:435` (dt at 445) | time_stepper | context | - |
| `Linear solve did not converge due to <REASON> iterations <n>` | PETSc 3.25.2, with `-ksp_converged_reason` | linear_solver | failure | `linear_solve` |
| `Nonlinear solve did not converge due to <REASON> iterations <n>` | PETSc 3.25.2, with `-snes_converged_reason` | nonlinear_solver | failure | `nonlinear_solve` |
| `Solve Did NOT Converge!` | MOOSE `framework/src/executioners/FEProblemSolve.C:505` | time_stepper | downstream | - |
| `Aborting as solve did not converge` | MOOSE `framework/src/executioners/TransientBase.C:511` (steady: `SteadyBase.C:74`) | time_stepper | downstream | - |
| `Solve failed and timestep already at or below dtmin, cannot continue!` | MOOSE `framework/src/timesteppers/TimeStepper.C:210` | time_stepper | terminal | `timestep_at_or_below_dtmin` |

## Columns

- **Message pattern**: the line after indentation and color codes are removed. The exact regex is in `lexicon.yaml` and must match the extractor's patterns in `events.py` (a test checks this).
- **Printed by**: the file and line at MOOSE commit `c2dfd9fe` that prints the message. The two reason lines come from PETSc: their exact text is in the PETSc 3.25.2 library, and MOOSE turns both options on as `::failed` unless the input sets them (`framework/src/utils/PetscSupport.C:832-845`), so PETSc prints a reason line whenever a solve fails. Checked on 2026-11-20 (issue #8).
- **Component**: the part of the solver the message belongs to.
- **Role**: `context` marks an attempt, `failure` is a cause, `downstream` is a consequence of an earlier failure, `terminal` is the last line, where the run gives up.
- **Label**: the identifier a correct answer uses. These are this project's draft labels, open for review, not an official benchmark vocabulary.

`time_stepping` is the third possible failure stage. No row here makes it a first failure, so it serves as the plausible wrong answer when checking that scoring tells a right answer from a wrong one.

## Adding a row

Add a row only for a message seen in real output, and note the run that showed it. A run with a failure-looking line that matches no row is rejected, never labeled by guesswork.

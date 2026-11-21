from datetime import date
from pathlib import Path

from mutant_forge.events import extract_events
from mutant_forge.lexicon import Lexicon, label
from mutant_forge.runner import RunResult
from mutant_forge.writer import CaseSpec, RunMeta

FIXTURES = Path(__file__).parent / "fixtures"

# The 11 solver messages in fixtures/d1_like.log, in order.
D1_EVENTS = [
    "Time Step 1, time = 2, dt = 2",
    "Linear solve did not converge due to DIVERGED_ITS iterations 0",
    "Nonlinear solve did not converge due to DIVERGED_LINE_SEARCH iterations 0",
    "Solve Did NOT Converge!",
    "Aborting as solve did not converge",
    "Time Step 1, time = 1, dt = 1",
    "Linear solve did not converge due to DIVERGED_ITS iterations 0",
    "Nonlinear solve did not converge due to DIVERGED_LINE_SEARCH iterations 0",
    "Solve Did NOT Converge!",
    "Aborting as solve did not converge",
    "Solve failed and timestep already at or below dtmin, cannot continue!",
]

# A run whose first failure is in the nonlinear solver.
NONLINEAR_EVENTS = [
    "Time Step 1, time = 1, dt = 1",
    "Nonlinear solve did not converge due to DIVERGED_MAX_IT iterations 1",
    "Solve Did NOT Converge!",
    "Aborting as solve did not converge",
    "Solve failed and timestep already at or below dtmin, cannot continue!",
]


def read(name: str) -> str:
    # read_bytes keeps "\r\n"; read_text would turn it into "\n" and hide the CRLF case
    return (FIXTURES / name).read_bytes().decode("utf-8")


def d1_spec() -> CaseSpec:
    """A complete CaseSpec for a D1-like case, built from the fixture log."""
    raw = read("d1_like.log")
    run = RunResult(1, None, False, raw, extract_events(raw), [], 1.0)
    return CaseSpec(
        case_id="D1-MF-DIFF1DT-F1-001",
        base_problem_id="MF-DIFF1DT-BASE-001",
        title="Draft (generated): linear solve failure before dtmin",
        physics_domains=["thermal_energy_transport"],
        failing_input=(Path(__file__).parents[1] / "bases" / "diff1dt.i").read_text(),
        events=D1_EVENTS,
        exit_code=1,
        labels=label(D1_EVENTS, Lexicon.load()),
        timestep_attempts=[2.0, 1.0],
        runs=[run, run, run],
        meta=RunMeta(
            executable="modules/combined/combined-opt",
            moose_revision="c2dfd9fedd3193740a5278ec32269450c618e3b7",
            petsc_version="3.25.2",
            command="combined-opt -i failing.i --color off",
            captured_on=date(2026, 11, 20),
            platform="Linux test-host",
        ),
    )

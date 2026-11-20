from pathlib import Path

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

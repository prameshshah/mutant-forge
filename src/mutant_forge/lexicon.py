"""Name each solver message, then label a run by its first failure and its last line."""

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

STAGE_OF = {
    "linear_solver": "linear_solve",
    "nonlinear_solver": "nonlinear_solve",
    "time_stepper": "time_stepping",
}
DEFAULT_PATH = Path(__file__).with_name("lexicon.yaml")


@dataclass(frozen=True)
class Row:
    id: str
    pattern: str
    component: str
    role: str  # context, failure, downstream or terminal
    symptom: str | None
    token: str  # the word a correct answer must quote; "{reason}" means the PETSc reason code
    source: str


@dataclass(frozen=True)
class Lexicon:
    rows: list[Row]

    @classmethod
    def load(cls, path: Path | None = None) -> "Lexicon":
        data = yaml.safe_load((path or DEFAULT_PATH).read_text())
        return cls([Row(**row) for row in data["rows"]])

    def match(self, message: str) -> Row | None:
        return next((r for r in self.rows if re.fullmatch(r.pattern, message)), None)

    def stages(self) -> list[str]:
        return sorted(STAGE_OF.values())

    def symptoms(self) -> list[str]:
        return sorted({r.symptom for r in self.rows if r.symptom})


@dataclass(frozen=True)
class Labels:
    failure_stage: str
    terminal_symptom: str
    first_event: str
    terminal_event: str
    wrong_stage: str  # a plausible wrong answer, to check that scoring tells them apart


class LabelError(Exception):
    def __init__(self, reason: str, detail: str):
        super().__init__(f"{reason}: {detail}")
        self.reason = reason


def label(events: list[str], lexicon: Lexicon) -> Labels:
    rows = []
    for event in events:
        row = lexicon.match(event)
        if row is None:
            raise LabelError("label_unknown", event)
        rows.append(row)

    first = next((i for i, r in enumerate(rows) if r.role == "failure"), None)
    if first is None:
        raise LabelError("no_first_failure", "no failure line in the run")
    last = rows[-1]
    if last.role != "terminal" or not last.symptom:
        raise LabelError("no_terminal_symptom", events[-1])

    failure_stage = STAGE_OF[rows[first].component]
    wrong_stage = STAGE_OF[last.component]
    if wrong_stage == failure_stage:
        wrong_stage = next(s for s in sorted(STAGE_OF.values()) if s != failure_stage)
    return Labels(
        failure_stage=failure_stage,
        terminal_symptom=last.symptom,
        first_event=events[first],
        terminal_event=events[-1],
        wrong_stage=wrong_stage,
    )


def evidence_token(message: str, row: Row) -> str:
    if row.token == "{reason}":
        return re.search(r"due to (\w+)", message).group(1)
    return row.token

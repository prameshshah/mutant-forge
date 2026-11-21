"""The four injected faults, and the run plan that says which base each one breaks."""

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from mutant_forge.hitedit import remove_block, set_param

BASE_KINDS = {
    "diff1dt": {"transient"},
    "diff2ds": {"steady"},
    "nlheat1dt": {"transient", "nonlinear"},
    "nlheat2dt": {"transient", "nonlinear"},
}

STEP = {"dt": "Executioner/dt", "dtmin": "Executioner/dtmin"}


@dataclass(frozen=True)
class Fault:
    id: str
    description: str
    intended_stage: str
    needs: str  # transient, steady or nonlinear
    params: dict[str, str]  # spec parameter -> input path it sets
    fixed: dict[str, str] = field(default_factory=dict)  # input path -> value
    remove: tuple[str, ...] = ()  # blocks deleted from the input


@dataclass(frozen=True)
class FaultSpec:
    spec_id: str
    base: str
    fault_id: str
    params: dict[str, str]


class FaultNotApplicable(Exception):
    pass


FAULTS = {
    "F1": Fault(
        id="F1",
        description="linear solver allowed zero iterations, so steps are cut back to dtmin",
        intended_stage="linear_solve",
        needs="transient",
        params=STEP,
        fixed={
            "Executioner/petsc_options_iname": "'-ksp_max_it'",
            "Executioner/petsc_options_value": "'0'",
        },
    ),
    "F2": Fault(
        id="F2",
        description="Newton allowed one iteration",
        intended_stage="nonlinear_solve",
        needs="nonlinear",
        params=STEP,
        fixed={"Executioner/nl_max_its": "1"},
    ),
    "F3": Fault(
        id="F3",
        description="nonlinear tolerances too tight to reach",
        intended_stage="nonlinear_solve",
        needs="nonlinear",
        params={
            "nl_rel_tol": "Executioner/nl_rel_tol",
            "nl_abs_tol": "Executioner/nl_abs_tol",
            "nl_max_its": "Executioner/nl_max_its",
            **STEP,
        },
    ),
    "F4": Fault(
        id="F4",
        description="boundary conditions removed from a steady problem",
        intended_stage="linear_solve",
        needs="steady",
        params={"nx": "Mesh/nx", "ny": "Mesh/ny"},
        remove=("BCs",),
    ),
}


def apply_fault(base_text: str, base_kind: set[str], spec: FaultSpec) -> str:
    fault = FAULTS[spec.fault_id]
    if fault.needs not in base_kind:
        raise FaultNotApplicable(f"{spec.spec_id}: {fault.id} needs a {fault.needs} base")
    if set(spec.params) != set(fault.params):
        raise ValueError(
            f"{spec.spec_id}: {fault.id} takes {sorted(fault.params)}, got {sorted(spec.params)}"
        )
    text = base_text
    for block in fault.remove:
        text = remove_block(text, block)
    for path, value in fault.fixed.items():
        text = set_param(text, path, value)
    for name, path in fault.params.items():
        text = set_param(text, path, spec.params[name])
    return text


def load_plan(path: Path) -> list[FaultSpec]:
    specs = yaml.safe_load(path.read_text(encoding="utf-8"))["specs"]
    # str() because YAML reads 2 as an int; MOOSE input values are text
    return [
        FaultSpec(s["id"], s["base"], s["fault"], {k: str(v) for k, v in s["params"].items()})
        for s in specs
    ]

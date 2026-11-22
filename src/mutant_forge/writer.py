"""Write one draft D1-format case in the benchmark's schema 2.0 folder layout."""

import hashlib
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import yaml

from mutant_forge.lexicon import Labels, Lexicon
from mutant_forge.runner import RunResult, consistent

TEMPLATE = Path(__file__).with_name("templates") / "prompt_d1.md"
BUDGET = {
    "wall_time_seconds": 60,
    "cpu_seconds": 30,
    "memory_mib": 512,
    "validation_attempts": 0,
    "execution_attempts": 0,
}


@dataclass(frozen=True)
class RunMeta:
    executable: str
    moose_revision: str
    petsc_version: str
    command: str
    captured_on: date
    platform: str


@dataclass(frozen=True)
class CaseSpec:
    case_id: str
    base_problem_id: str
    title: str
    physics_domains: list[str]
    failing_input: str
    events: list[str]
    exit_code: int
    labels: Labels
    timestep_attempts: list[float]
    runs: list[RunResult]
    meta: RunMeta


def case_id_for(base: str, fault_id: str, n: int) -> str:
    return f"D1-MF-{base.upper()}-{fault_id}-{n:03d}"


def gold_response(spec: CaseSpec) -> dict:
    labels = spec.labels
    return {
        "claim": {
            "failure_stage": labels.failure_stage,
            "terminal_symptom": labels.terminal_symptom,
        },
        "evidence": [
            {
                "source_id": "solver_events",
                "observation": labels.first_event,
                "interpretation": f"The first failure, in the {labels.failure_stage} stage.",
            },
            {
                "source_id": "solver_events",
                "observation": labels.terminal_event,
                "interpretation": "The run stops here, as a consequence of the earlier failure.",
            },
        ],
    }


def wrong_stage_response(spec: CaseSpec) -> dict:
    response = gold_response(spec)
    response["claim"]["failure_stage"] = spec.labels.wrong_stage
    return response


def _write(path: Path, text: str) -> str:
    """Write text as UTF-8 with the given line endings and return its sha256."""
    data = text.encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def _write_json(path: Path, data: dict) -> str:
    return _write(path, json.dumps(data, indent=2) + "\n")


def _write_yaml(path: Path, data: dict) -> str:
    return _write(path, yaml.safe_dump(data, sort_keys=False))


def _number(x: float) -> float | int:
    return int(x) if float(x).is_integer() else x


def write_case(spec: CaseSpec, root: Path, lexicon: Lexicon) -> None:
    case_dir = root / "public" / "cases" / spec.case_id
    private = root / "private" / "cases" / spec.case_id
    labels = spec.labels

    # each hash is taken from the bytes written, before the file that lists it is written
    failing = _write(case_dir / "artifacts" / "failing.i", spec.failing_input)
    events = _write_json(
        case_dir / "evidence" / "solver-events.json",
        {
            "schema_version": "1.0",
            "case_id": spec.case_id,
            "exit_code": spec.exit_code,
            "ordered_events": [{"order": i, "message": m} for i, m in enumerate(spec.events, 1)],
        },
    )
    meta = _write_json(
        case_dir / "evidence" / "run-metadata.json",
        {
            "schema_version": "1.0",
            "case_id": spec.case_id,
            "captured_on": spec.meta.captured_on.isoformat(),
            "executable": spec.meta.executable,
            "moose_revision": spec.meta.moose_revision,
            "petsc_version": spec.meta.petsc_version,
            "command": spec.meta.command,
            "process_count": 1,
            "repetitions": len(spec.runs),
            "expected_exit_code": spec.exit_code,
            "timestep_attempts": [_number(t) for t in spec.timestep_attempts],
            "sha256": {"artifacts/failing.i": failing, "evidence/solver-events.json": events},
        },
    )
    template = TEMPLATE.read_text(encoding="utf-8")
    prompt = _write(
        case_dir / "prompt.md",
        template.replace("{stages}", ", ".join(lexicon.stages())).replace(
            "{symptoms}", ", ".join(lexicon.symptoms())
        ),
    )
    _write_yaml(
        case_dir / "case.yaml",
        {
            "schema_version": "2.0",
            "case_id": spec.case_id,
            "title": spec.title,
            "case_kind": "atomic",
            "track": "DIAG",
            "subcategory": "D1",
            "difficulty": "L2",
            "scoring_profile": "balanced_v1",
            "base_problem_id": spec.base_problem_id,
            "physics_domains": spec.physics_domains,
            "target": {
                "application": "combined",
                "version": spec.meta.moose_revision,
                "executable_hint": "combined-opt",
            },
            "prompt_path": "prompt.md",
            "prompt_sha256": prompt,
            "artifacts": [
                {
                    "id": "failing_input",
                    "path": "artifacts/failing.i",
                    "role": "immutable_input",
                    "mutable": False,
                    "required": True,
                    "sha256": failing,
                }
            ],
            "evidence_sources": [
                {
                    "id": "solver_events",
                    "path": "evidence/solver-events.json",
                    "kind": "ordered_moose_solver_events",
                    "description": "Solver messages in the order the pinned run printed them",
                    "sha256": events,
                },
                {
                    "id": "run_metadata",
                    "path": "evidence/run-metadata.json",
                    "kind": "reproducibility_metadata",
                    "description": "Build revision, PETSc version, command and file hashes",
                    "sha256": meta,
                },
            ],
            "starting_state": {
                "description": "A MOOSE input and the ordered solver messages of its run.",
                "supplied_truth": [
                    "The input was run unchanged with the pinned combined-opt build.",
                    "The messages keep the order in which the run printed them.",
                ],
                "excluded_from_scoring": ["Input repair", "Solver retuning"],
            },
            "actions": {
                "permitted": [
                    "Read the supplied input and solver messages.",
                    "Report the earliest failing stage and the terminal symptom.",
                ],
                "prohibited": [
                    "Modify or run the input.",
                    "Read private evaluation or reproduction files.",
                ],
            },
            "budget": BUDGET,
            "submission": {
                "response_mode": "structured_json",
                "required_claim_paths": ["/claim/failure_stage", "/claim/terminal_symptom"],
                "evidence_required": True,
                "required_artifacts": [],
                "maximum_artifacts": 0,
            },
            "required_stages": [],
        },
    )

    _write_yaml(
        private / "evaluation.yaml",
        {
            "schema_version": "2.0",
            "case_id": spec.case_id,
            "evaluator": "structured_claim_v2",
            "capability_criteria": [
                {
                    "id": "failure_stage",
                    "weight": 0.5,
                    "description": "Names the stage of the first failure message.",
                    "json_pointer": "/claim/failure_stage",
                    "comparator": "normalized_exact",
                    "expected": labels.failure_stage,
                },
                {
                    "id": "terminal_symptom",
                    "weight": 0.5,
                    "description": "Names the symptom of the last message.",
                    "json_pointer": "/claim/terminal_symptom",
                    "comparator": "normalized_exact",
                    "expected": labels.terminal_symptom,
                },
            ],
            "evidence_criteria": [
                {
                    "id": "first_failure_observation",
                    "weight": 0.5,
                    "description": "The first evidence entry quotes the first failure message.",
                    "json_pointer": "/evidence/0/observation",
                    "comparator": "contains",
                    "expected": labels.first_token,
                },
                {
                    "id": "terminal_observation",
                    "weight": 0.5,
                    "description": "The second evidence entry quotes the terminal message.",
                    "json_pointer": "/evidence/1/observation",
                    "comparator": "contains",
                    "expected": labels.terminal_token,
                },
            ],
            "hard_gates": [],
        },
    )
    _write(
        private / "reproduction.md",
        "# Reproduction\n\n"
        f"- MOOSE revision: {spec.meta.moose_revision}\n"
        f"- PETSc: {spec.meta.petsc_version}\n"
        f"- Executable: {spec.meta.executable}\n"
        "- MPI processes: 1\n"
        f"- Expected exit code: {spec.exit_code}\n"
        f"- Command: `{spec.meta.command}`\n"
        f"- Platform: {spec.meta.platform}\n"
        f"- Captured: {spec.meta.captured_on.isoformat()}\n",
    )
    home = str(Path.home())
    for k, run in enumerate(spec.runs, 1):
        # stack traces name the MOOSE build under the home folder; keep that path private
        log = run.output.replace(home, "~") if len(home) > 1 else run.output
        _write(private / "validation" / f"run-{k}.log", log)
        _write(private / "validation" / f"run-{k}.status", f"{run.exit_code}\n")
    _write_json(
        private / "validation-summary.json",
        {
            "repetitions": len(spec.runs),
            "consistent": consistent(spec.runs),
            "exit_codes": [run.exit_code for run in spec.runs],
            "event_count": len(spec.events),
        },
    )

    examples = root / "example-submissions"
    _write_json(examples / spec.case_id / "response.json", gold_response(spec))
    _write_json(
        examples / f"{spec.case_id}-mutant-001" / "response.json", wrong_stage_response(spec)
    )


def write_manifest(root: Path, case_ids: list[str]) -> Path:
    path = root / "manifest.yaml"
    _write_yaml(
        path,
        {
            "schema_version": "2.0",
            "benchmark_id": "mutant-forge-drafts",
            "benchmark_version": "0.1.0",
            "required_atomic_subcategories": ["D1"],
            "cases": [
                {
                    "case_id": case_id,
                    "public_case": f"public/cases/{case_id}/case.yaml",
                    "private_evaluation": f"private/cases/{case_id}/evaluation.yaml",
                    "split": "development",
                    "enabled": True,
                }
                for case_id in case_ids
            ],
        },
    )
    return path

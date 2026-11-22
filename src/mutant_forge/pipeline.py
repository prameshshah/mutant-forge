"""Turn one fault spec into a kept draft case, or into a rejection with a named reason."""

import hashlib
import json
import os
import platform
import shutil
import subprocess
import tempfile
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import date
from enum import StrEnum
from pathlib import Path

from mutant_forge import bench
from mutant_forge.faults import BASE_KINDS, FAULTS, FaultNotApplicable, FaultSpec, apply_fault
from mutant_forge.lexicon import LabelError, Lexicon, label
from mutant_forge.runner import check_input, consistent, repeat, run_moose
from mutant_forge.writer import CaseSpec, RunMeta, case_id_for, write_case, write_manifest

TITLE_PREFIX = "Draft (generated): "


class Reason(StrEnum):
    BASE_NOT_CLEAN = "base_not_clean"
    PARSE_FAILED = "parse_failed"
    NO_FAILURE = "no_failure"
    CRASH = "crash"
    TIMEOUT = "timeout"
    NONDETERMINISTIC = "nondeterministic"
    UNCLASSIFIED_MESSAGE = "unclassified_message"
    LABEL_UNKNOWN = "label_unknown"
    NO_FIRST_FAILURE = "no_first_failure"
    NO_TERMINAL_SYMPTOM = "no_terminal_symptom"
    WRONG_CAUSE = "wrong_cause"
    DUPLICATE = "duplicate"
    SELF_CHECK_FAILED = "self_check_failed"


@dataclass(frozen=True)
class Outcome:
    spec_id: str
    base: str
    fault_id: str
    status: str  # kept or rejected
    reason: Reason | None = None
    failure_stage: str | None = None
    terminal_symptom: str | None = None
    case_id: str | None = None
    signature: str | None = None
    detail: str | None = None


@dataclass(frozen=True)
class Config:
    exe: Path
    executable: str  # as written in run-metadata.json
    bases_dir: Path
    moose_revision: str
    petsc_version: str
    base_kinds: dict[str, set[str]] = field(default_factory=lambda: dict(BASE_KINDS))
    timeout_s: int = 60

    @classmethod
    def from_env(cls, bases_dir: Path = Path("bases")) -> "Config":
        exe = Path(os.environ["MF_MOOSE_EXE"])
        moose_dir = Path(os.environ["MF_MOOSE_DIR"])
        git = ["git", "-C", str(moose_dir), "rev-parse", "HEAD"]
        revision = subprocess.run(git, capture_output=True, text=True, check=True).stdout.strip()
        executable = str(exe.relative_to(moose_dir)) if exe.is_relative_to(moose_dir) else exe.name
        return cls(exe, executable, bases_dir, revision, os.environ["MF_PETSC_VERSION"])


@dataclass
class Seen:
    """What is already kept: message signatures, counts per base|fault, and case IDs."""

    signatures: set[str] = field(default_factory=set)
    per_family: Counter[str] = field(default_factory=Counter)
    case_ids: list[str] = field(default_factory=list)


def _remove_case(root: Path, case_id: str) -> None:
    for folder in (
        root / "public" / "cases" / case_id,
        root / "private" / "cases" / case_id,
        root / "example-submissions" / case_id,
        root / "example-submissions" / f"{case_id}-mutant-001",
    ):
        shutil.rmtree(folder, ignore_errors=True)


def generate_one(spec: FaultSpec, cfg: Config, root: Path, seen: Seen, cap: int = 2) -> Outcome:
    def reject(reason: Reason, detail: str | None = None, **found) -> Outcome:
        return Outcome(
            spec.spec_id, spec.base, spec.fault_id, "rejected", reason, detail=detail, **found
        )

    base_file = cfg.bases_dir / f"{spec.base}.i"
    clean = run_moose(cfg.exe, base_file, timeout_s=cfg.timeout_s)
    header_only = all(e.startswith("Time Step") for e in clean.events)
    if clean.exit_code != 0 or not header_only or clean.unclassified:
        return reject(Reason.BASE_NOT_CLEAN)

    try:
        text = apply_fault(base_file.read_text(encoding="utf-8"), cfg.base_kinds[spec.base], spec)
    except FaultNotApplicable as e:
        return reject(Reason.PARSE_FAILED, str(e))

    with tempfile.TemporaryDirectory(prefix="mf-input-") as work:
        failing = Path(work) / "failing.i"
        failing.write_text(text, encoding="utf-8")
        if check_input(cfg.exe, failing).exit_code != 0:
            return reject(Reason.PARSE_FAILED, "--check-input failed")
        runs = repeat(cfg.exe, failing, timeout_s=cfg.timeout_s)

    if any(r.timed_out for r in runs):
        return reject(Reason.TIMEOUT)
    if any(r.signal is not None or r.exit_code not in (0, 1) for r in runs):
        return reject(Reason.CRASH)
    if all(r.exit_code == 0 for r in runs):
        return reject(Reason.NO_FAILURE)
    if not consistent(runs):
        return reject(Reason.NONDETERMINISTIC)
    if any(r.unclassified for r in runs):
        lines = [line for r in runs for line in r.unclassified]
        return reject(Reason.UNCLASSIFIED_MESSAGE, "; ".join(lines))

    events, lexicon = runs[0].events, Lexicon.load()
    try:
        labels = label(events, lexicon)
    except LabelError as e:
        return reject(Reason(e.reason), str(e))
    found = {"failure_stage": labels.failure_stage, "terminal_symptom": labels.terminal_symptom}
    if labels.failure_stage != FAULTS[spec.fault_id].intended_stage:
        return reject(Reason.WRONG_CAUSE, **found)

    # the messages alone decide a duplicate: identical evidence on another base is not a new case
    signature = hashlib.sha256("\n".join(events).encode("utf-8")).hexdigest()
    family = f"{spec.base}|{spec.fault_id}"
    if signature in seen.signatures or seen.per_family[family] >= cap:
        return reject(Reason.DUPLICATE, signature=signature, **found)

    case_id = case_id_for(spec.base, spec.fault_id, seen.per_family[family] + 1)
    case = CaseSpec(
        case_id=case_id,
        base_problem_id=f"MF-{spec.base.upper()}-BASE-001",
        title=f"{TITLE_PREFIX}{FAULTS[spec.fault_id].description} ({spec.base})",
        physics_domains=["thermal_energy_transport"],
        failing_input=text,
        events=events,
        exit_code=runs[0].exit_code,
        labels=labels,
        timestep_attempts=[float(e.rsplit("dt = ", 1)[1]) for e in events if e.startswith("Time")],
        runs=runs,
        meta=RunMeta(
            executable=cfg.executable,
            moose_revision=cfg.moose_revision,
            petsc_version=cfg.petsc_version,
            command="combined-opt -i failing.i --color off",
            captured_on=date.today(),
            platform=platform.platform(),
        ),
    )
    write_case(case, root, lexicon)
    manifest = write_manifest(root, [*seen.case_ids, case_id])
    try:
        bench.validate(manifest)
        check = bench.self_check(manifest, case_id, root)
        detail = None if check.ok else f"self-check: {check}"
    except bench.BenchError as e:
        detail = str(e)
    if detail is not None:
        _remove_case(root, case_id)
        write_manifest(root, seen.case_ids)
        return reject(
            Reason.SELF_CHECK_FAILED, detail, case_id=case_id, signature=signature, **found
        )

    seen.signatures.add(signature)
    seen.per_family[family] += 1
    seen.case_ids.append(case_id)
    return Outcome(
        spec.spec_id,
        spec.base,
        spec.fault_id,
        "kept",
        case_id=case_id,
        signature=signature,
        **found,
    )


def run_all(plan: list[FaultSpec], cfg: Config, root: Path) -> list[Outcome]:
    """Run every spec into an empty folder and write one outcomes.jsonl line per spec."""
    if root.exists() and any(root.iterdir()):
        raise ValueError(f"{root} is not empty; choose a new output folder")
    root.mkdir(parents=True, exist_ok=True)
    seen = Seen()
    outcomes = [generate_one(spec, cfg, root, seen) for spec in plan]
    with (root / "outcomes.jsonl").open("w", encoding="utf-8") as f:
        for outcome in outcomes:
            f.write(json.dumps(asdict(outcome)) + "\n")
    return outcomes

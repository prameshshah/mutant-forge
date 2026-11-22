"""Command line: mutant-forge generate | run-all."""

import argparse
from collections import Counter
from pathlib import Path

from mutant_forge.faults import load_plan
from mutant_forge.pipeline import Config, run_all


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mutant-forge")
    commands = parser.add_subparsers(dest="command", required=True)
    generate = commands.add_parser("generate", help="run one spec from the plan")
    generate.add_argument("--spec-id", required=True)
    every = commands.add_parser("run-all", help="run every spec in the plan")
    for p in (generate, every):
        p.add_argument("--plan", type=Path, required=True)
        p.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    plan = load_plan(args.plan)
    if args.command == "generate":
        plan = [s for s in plan if s.spec_id == args.spec_id]
        if not plan:
            parser.error(f"no spec {args.spec_id!r} in {args.plan}")
    outcomes = run_all(plan, Config.from_env(), args.out)

    for o in outcomes:
        print(" ".join(x for x in (o.spec_id, o.status, o.reason, o.case_id) if x))
    totals = Counter(o.reason or o.status for o in outcomes)
    print("total:", ", ".join(f"{k} {v}" for k, v in sorted(totals.items())))
    return 0

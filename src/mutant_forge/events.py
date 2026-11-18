"""Pull the ordered solver messages out of MOOSE console output."""

import re

# A line is an event only if, after normalize_line, it fully matches one of these.
# docs/event-rule.md (issue #8) explains the rule against a real run.
KEEP_PATTERNS = [
    re.compile(p)
    for p in (
        r"^Time Step \d+, time = \S+, dt = \S+$",
        r"^Linear solve did not converge due to \w+ iterations \d+$",
        r"^Nonlinear solve did not converge due to \w+ iterations \d+$",
        r"^Solve Did NOT Converge!$",
        r"^Aborting as solve did not converge$",
        r"^Solve failed and timestep already at or below dtmin, cannot continue!$",
    )
]

# Words that suggest a failure; \bnan\b so "dominant" or "tmpnan3k" do not match.
FAILURE_WORDS = re.compile(
    r"(?i)error|diverged|did not converge|failed|\bnan\b|zero pivot|segmentation"
)

ANSI_COLOR = re.compile(r"\x1b\[[0-9;]*m")
ERROR_BANNER = "*** ERROR ***"  # mooseError prints this line before its message
DTMIN = "Solve failed and timestep already at or below dtmin, cannot continue!"


def normalize_line(line: str) -> str:
    # split() also drops "\r" and collapses indentation and repeated spaces
    return " ".join(ANSI_COLOR.sub("", line).split())


def _is_event(line: str) -> bool:
    return any(p.fullmatch(line) for p in KEEP_PATTERNS)


def extract_events(raw: str) -> list[str]:
    lines = (normalize_line(line) for line in raw.splitlines())
    return [line for line in lines if _is_event(line)]


def unclassified_failure_lines(raw: str) -> list[str]:
    found = []
    for line in map(normalize_line, raw.splitlines()):
        if line == DTMIN:
            break  # the stack trace printed after a mooseError contains "error"
        if line != ERROR_BANNER and not _is_event(line) and FAILURE_WORDS.search(line):
            found.append(line)
    return found

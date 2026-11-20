"""Edit MOOSE input files line by line, for the simple subset our bases use.

Supported: nested [Name] ... [] blocks, `key = value` lines, and full-line # comments.
Anything else raises HitEditError instead of being guessed at.
"""

import re
from dataclasses import dataclass

HEADER = re.compile(r"\[([^\[\]]+)\]")
PARAM = re.compile(r"([A-Za-z_][\w:-]*)\s*=\s*(.*)")


class HitEditError(Exception):
    pass


@dataclass(frozen=True)
class _Block:
    start: int  # index of the [Name] line
    end: int  # index of its closing [] line
    indent: str


def _indent(line: str) -> str:
    return line[: len(line) - len(line.lstrip())]


def _scan(text: str) -> tuple[dict[str, tuple[int, str]], dict[str, _Block]]:
    """Map each parameter path to (line index, value), and each block path to its lines."""
    found: dict[str, tuple[int, str]] = {}
    blocks: dict[str, _Block] = {}
    stack: list[tuple[str, int, str]] = []  # (block path, start line, indent)
    for i, line in enumerate(text.splitlines()):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if s == "[]":
            if not stack:
                raise HitEditError(f"line {i + 1}: [] without an open block")
            path, start, indent = stack.pop()
            blocks[path] = _Block(start, i, indent)
        elif m := HEADER.fullmatch(s):
            parent = stack[-1][0] + "/" if stack else ""
            stack.append((parent + m.group(1), i, _indent(line)))
        elif (m := PARAM.fullmatch(s)) and stack:
            # shortcut: an inline "# comment" stays part of the value; our bases have none
            found[f"{stack[-1][0]}/{m.group(1)}"] = (i, m.group(2))
        else:
            raise HitEditError(f"line {i + 1}: cannot read {s!r}")
    if stack:
        raise HitEditError(f"block {stack[-1][0]!r} is never closed")
    return found, blocks


def params(text: str) -> dict[str, str]:
    return {path: value for path, (_, value) in _scan(text)[0].items()}


def set_param(text: str, path: str, value: str) -> str:
    found, blocks = _scan(text)
    lines = text.splitlines(keepends=True)
    block, _, key = path.rpartition("/")
    if path in found:
        i = found[path][0]
        lines[i] = f"{_indent(lines[i])}{key} = {value}\n"
    elif block in blocks:
        b = blocks[block]
        lines.insert(b.end, f"{b.indent}  {key} = {value}\n")
    else:
        raise HitEditError(f"no block {block!r} for {path!r}")
    return "".join(lines)


def remove_param(text: str, path: str) -> str:
    found, _ = _scan(text)
    if path not in found:
        raise HitEditError(f"no parameter {path!r}")
    lines = text.splitlines(keepends=True)
    del lines[found[path][0]]
    return "".join(lines)


def remove_block(text: str, path: str) -> str:
    _, blocks = _scan(text)
    if path not in blocks:
        raise HitEditError(f"no block {path!r}")
    b = blocks[path]
    lines = text.splitlines(keepends=True)
    del lines[b.start : b.end + 1]
    return "".join(lines)


def changed_paths(before: str, after: str) -> set[str]:
    a, b = params(before), params(after)
    return {k for k in a.keys() | b.keys() if a.get(k) != b.get(k)}

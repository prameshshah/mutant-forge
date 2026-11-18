## What
<!-- one or two lines -->

## Why
<!-- the task, and why this approach -->

Closes #

## How I checked it
- [ ] `uv run black --check . && uv run ruff check . && uv run pytest -q`
- [ ] Marked tests run locally if this touches MOOSE or the benchmark CLI (`-m moose`, `-m bench`)
- [ ] No `.env`, `out/`, or files from the benchmark's private folders in the diff

## Notes
<!-- anything surprising, a known limit, a follow-up issue -->

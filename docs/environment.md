# Environment

Recorded 2026-11-18 (issue #1). Every value below was read from the machine, not assumed.

## Machine
- Intel Core i7-1255U (10 cores, 12 threads), Windows 11 + WSL2
- Ubuntu 24.04.3 LTS, kernel 6.6.87.2-microsoft-standard-WSL2
- WSL limits (`.wslconfig`): memory=10GB (Ubuntu sees 9 GB), swap=16GB

## MOOSE
- Source: `~/projects/moose`, commit `c2dfd9fedd3193740a5278ec32269450c618e3b7` ("Merge pull request #33555 from NamjaeChoi/kokkos_sycl")
- Conda env `moose` (Miniforge, conda 26.10.0, INL channel first):
  - moose-dev 2026.07.30 (mpich), the version `scripts/versioner.py moose-dev` printed
  - moose-petsc 3.25.2
  - moose-libmesh 2026.06.05_ab36c00
  - moose-wasp 2026.06.15_d8777a8
  - compiler: conda-forge gcc 14.4.0
- Build: `modules/combined`, `make -j 4`, opt mode
  - wall time 81m14.652s (user 296m30s, sys 26m16s), 0 compile errors
  - `du -sh ~/projects/moose` after build: 2.7G
- Executable: `~/projects/moose/modules/combined/combined-opt`
  - `--check-input` present; `--color <auto,on,off=on>` present, so the runner can pass `--color off`
- Smoke run: `test/tests/kernels/simple_diffusion/simple_diffusion.i` with `Outputs/exodus=false --color off` in a temp folder: `Solve Converged!`, exit 0, no files written, MOOSE checkout still clean

## Benchmark
- `~/projects/moose-agent-benchmark` at commit `5bf036c` (detached)
- uv 0.13.9, `uv sync --extra dev` (Python 3.12.3)
- `uv run moose-benchmark validate benchmark/manifest.yaml`: "validated 12 enabled case(s) in moose-agent-benchmark-development", exit 0

from pathlib import Path

import pytest

from mutant_forge.hitedit import (
    HitEditError,
    changed_paths,
    params,
    remove_block,
    remove_param,
    set_param,
)

BASE = """\
# a small input in the style of our bases
[Mesh]
  type = GeneratedMesh
  dim = 1
[]

[BCs]
  [left]
    type = DirichletBC
    boundary = left
    value = 0
  []
  [right]
    type = DirichletBC
    boundary = right
    value = 0
  []
[]

[Executioner]
  type = Transient
  num_steps = 1
  dt = 1
  petsc_options = '-ksp_converged_reason'
[]
"""


def test_params_reads_nested():
    assert params(BASE)["BCs/left/value"] == "0"


def test_set_existing():
    assert params(set_param(BASE, "Executioner/num_steps", "2"))["Executioner/num_steps"] == "2"


def test_set_new_inserts_inside_block():
    text = set_param(BASE, "Executioner/dtmin", "1")
    assert params(text)["Executioner/dtmin"] == "1"
    assert text.endswith("  dtmin = 1\n[]\n")


def test_quoted_value_kept():
    text = set_param(BASE, "Executioner/petsc_options_iname", "'-ksp_max_it'")
    assert params(text)["Executioner/petsc_options_iname"] == "'-ksp_max_it'"


def test_remove_param():
    assert "Executioner/dt" not in params(remove_param(BASE, "Executioner/dt"))


def test_remove_block():
    assert not any(k.startswith("BCs/left/") for k in params(remove_block(BASE, "BCs/left")))


def test_one_change_one_path():
    assert changed_paths(BASE, set_param(BASE, "Executioner/dt", "2")) == {"Executioner/dt"}


def test_missing_block_raises():
    with pytest.raises(HitEditError):
        set_param(BASE, "Nope/x", "1")


def test_bases_are_readable():
    # runs in CI, where the MOOSE tests in test_bases.py are skipped
    bases = sorted((Path(__file__).parents[1] / "bases").glob("*.i"))
    assert bases
    for path in bases:
        values = params(path.read_text(encoding="utf-8")).values()
        # the editor keeps an inline "# comment" as part of the value, so none may appear
        assert not any("#" in v for v in values), path.name

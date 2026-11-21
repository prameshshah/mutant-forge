import pytest
from helpers import d1_spec

from mutant_forge.bench import BenchError, self_check, validate
from mutant_forge.lexicon import Lexicon
from mutant_forge.writer import write_case, write_manifest

pytestmark = pytest.mark.bench


def test_her_tools_accept_and_discriminate(tmp_path):
    spec = d1_spec()
    write_case(spec, tmp_path, Lexicon.load())
    manifest = write_manifest(tmp_path, [spec.case_id])
    validate(manifest)
    sc = self_check(manifest, spec.case_id, tmp_path)
    assert sc.gold_official_score == 100.0 and sc.gold_passed and not sc.wrong_passed


def test_her_cli_failure_surfaces(tmp_path):
    (tmp_path / "manifest.yaml").write_text("not: a manifest\n")
    with pytest.raises(BenchError, match="schema_version"):
        validate(tmp_path / "manifest.yaml")

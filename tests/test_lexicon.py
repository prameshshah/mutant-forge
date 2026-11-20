import pytest
from helpers import D1_EVENTS, NONLINEAR_EVENTS

from mutant_forge.events import KEEP_PATTERNS
from mutant_forge.lexicon import LabelError, Lexicon, evidence_token, label

LEX = Lexicon.load()


def test_d1_labels():
    labels = label(D1_EVENTS, LEX)
    assert (labels.failure_stage, labels.terminal_symptom, labels.wrong_stage) == (
        "linear_solve",
        "timestep_at_or_below_dtmin",
        "time_stepping",
    )
    assert (labels.first_event, labels.terminal_event) == (D1_EVENTS[1], D1_EVENTS[-1])


def test_nonlinear_first():
    assert label(NONLINEAR_EVENTS, LEX).failure_stage == "nonlinear_solve"


def test_unknown_event_rejected():
    with pytest.raises(LabelError, match="label_unknown"):
        label(D1_EVENTS + ["Something new"], LEX)


def test_must_end_on_terminal():
    with pytest.raises(LabelError, match="no_terminal_symptom"):
        label(D1_EVENTS[:-1], LEX)


def test_no_failure_line_rejected():
    with pytest.raises(LabelError, match="no_first_failure"):
        label([D1_EVENTS[0], D1_EVENTS[-1]], LEX)


def test_evidence_token():
    assert evidence_token(D1_EVENTS[1], LEX.match(D1_EVENTS[1])) == "DIVERGED_ITS"


def test_vocabularies():
    assert LEX.stages() == ["linear_solve", "nonlinear_solve", "time_stepping"]
    assert LEX.symptoms() == ["timestep_at_or_below_dtmin"]


def test_patterns_match_the_extractor():
    assert sorted(r.pattern for r in LEX.rows) == sorted(p.pattern for p in KEEP_PATTERNS)


@pytest.mark.xfail(strict=True, reason="sources are added with the real-run check, issue #8")
def test_every_row_has_source():
    assert all(r.source for r in LEX.rows)

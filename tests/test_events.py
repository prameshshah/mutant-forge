from conftest import D1_EVENTS, read

from mutant_forge.events import extract_events, unclassified_failure_lines


def test_extracts_d1_events_in_order():
    assert extract_events(read("d1_like.log")) == D1_EVENTS


def test_noise_does_not_change_events():
    assert extract_events(read("d1_like_noise.log")) == extract_events(read("d1_like.log"))


def test_crlf_and_indent():
    assert extract_events(read("d1_like_crlf.log")) == D1_EVENTS


def test_extra_event_is_detected():
    assert extract_events(read("d1_like.log") + "\nSolve Did NOT Converge!\n") != D1_EVENTS


def test_unknown_failure_line_is_flagged():
    raw = read("d1_like.log").replace(
        "Solve failed and timestep",
        "[0]PETSC ERROR: Zero pivot in LU factorization\nSolve failed and timestep",
        1,
    )
    assert unclassified_failure_lines(raw) == ["[0]PETSC ERROR: Zero pivot in LU factorization"]


def test_known_lines_are_not_flagged():
    # includes the *** ERROR *** banner and the stack trace after the dtmin line
    assert unclassified_failure_lines(read("d1_like.log")) == []


def test_nan_is_a_word():
    raw = "Input File: /tmp/tmpnan3k/dominant.i\n0 Nonlinear |R| = -nan\n"
    assert unclassified_failure_lines(raw) == ["0 Nonlinear |R| = -nan"]

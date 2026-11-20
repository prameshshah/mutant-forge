from helpers import D1_EVENTS, read

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


def test_colored_log_has_no_unclassified_lines():
    assert unclassified_failure_lines(read("d1_like_noise.log")) == []


def test_other_moose_error_is_flagged():
    trace = "1: moose::internal::mooseErrorRaw(std::string, std::string, hit::Node const*, bool)"
    raw = (
        "*** ERROR ***\n"
        "The following occurred in the Kernel 'diff' of type Diffusion.\n\n"
        "Unable to find variable 'v'\n\n"
        "Stack frames: 2\n"
        "0: libMesh::print_trace(std::ostream&)\n" + trace + "\n"
    )
    # the message has no failure word, so the stack trace is what catches it
    assert unclassified_failure_lines(raw) == [trace]


def test_nan_is_a_word():
    raw = "Input File: /tmp/tmpnan3k/dominant.i\n0 Nonlinear |R| = -nan\n"
    assert unclassified_failure_lines(raw) == ["0 Nonlinear |R| = -nan"]

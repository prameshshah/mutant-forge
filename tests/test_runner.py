import signal

from helpers import D1_EVENTS

from mutant_forge.runner import check_input, consistent, repeat, run_moose


def test_d1_mode_exit_and_events(fake, inp):
    r = run_moose(fake, inp("d1"))
    assert (r.exit_code, r.events) == (1, D1_EVENTS)


def test_timeout_keeps_partial_output(fake, inp):
    r = run_moose(fake, inp("hang"), timeout_s=2)
    assert r.timed_out and r.exit_code is None
    assert r.events == ["Time Step 1, time = 2, dt = 2"]


def test_crash_reports_signal(fake, inp):
    r = run_moose(fake, inp("crash"))
    assert r.signal == signal.SIGSEGV and r.exit_code is None


def test_flaky_is_not_consistent(fake, inp):
    assert not consistent(repeat(fake, inp("flaky")))


def test_d1_is_consistent(fake, inp):
    assert consistent(repeat(fake, inp("d1")))


def test_no_runs_is_not_consistent():
    assert not consistent([])


def test_runs_are_isolated(fake, inp):
    f = inp("clean")
    run_moose(fake, f)
    assert not (f.parent / "out.e").exists()


def test_check_input_failure(fake, inp):
    assert check_input(fake, inp("badparse")).exit_code == 1

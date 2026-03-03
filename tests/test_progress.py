import time
import pytest
from pyplaner.progress import (
    QuietTracker, SimpleProgressTracker, TtyProgressTracker, create_tracker
)


def test_quiet_context_manager_noop():
    """QuietTracker context manager does nothing."""
    t = QuietTracker()
    with t("stage"):
        t.job("a")
        t.set_job_count(3)
        t.job("b")


def test_quiet_no_output(capsys):
    """QuietTracker produces no stdout output."""
    t = QuietTracker()
    with t("stage"):
        t.job("a")
    assert capsys.readouterr().out == ""


def test_simple_prints_stage_name(capsys):
    """Non-TTY tracker prints the stage name once."""
    t = SimpleProgressTracker()
    with t("Building"):
        t.job("step1")
        t.job("step2")
    out = capsys.readouterr().out
    assert "Building...\n" in out


def test_simple_records_job_durations():
    """Tracker stores (name, elapsed) for each job."""
    t = SimpleProgressTracker()
    with t("stage"):
        t.job("a")
        time.sleep(0.01)
        t.job("b")
        time.sleep(0.01)
    assert len(t.jobs) == 2
    assert t.jobs[0][0] == "a"
    assert t.jobs[1][0] == "b"
    assert all(d > 0 for _, d in t.jobs)


def test_simple_set_job_count():
    """set_job_count stores the value."""
    t = SimpleProgressTracker()
    with t("stage"):
        t.set_job_count(5)
        assert t.job_count == 5


def test_simple_exception_propagates():
    """Exceptions propagate out of the context manager."""
    t = SimpleProgressTracker()
    with pytest.raises(RuntimeError, match="boom"):
        with t("stage"):
            t.job("a")
            raise RuntimeError("boom")
    assert len(t.jobs) == 1


def test_tty_overwrites_line(capsys):
    """TTY tracker uses carriage-return to update the line."""
    t = TtyProgressTracker()
    with t("Gen"):
        t.job("a")
        t.job("b")
    out = capsys.readouterr().out
    assert "\r" in out


def test_tty_done_message(capsys):
    """TTY tracker prints 'done' on normal exit."""
    t = TtyProgressTracker()
    with t("Gen"):
        t.job("a")
    out = capsys.readouterr().out
    assert "done" in out


def test_tty_user_print_intercepted(capsys):
    """Prints inside the context appear without breaking the progress line."""
    t = TtyProgressTracker()
    with t("Gen"):
        t.job("a")
        print("hello from user")
    out = capsys.readouterr().out
    assert "hello from user" in out


def test_tty_stdout_restored_after_exit():
    """sys.stdout is restored to original after __exit__."""
    import sys
    original = sys.stdout
    t = TtyProgressTracker()
    with t("Gen"):
        pass
    assert sys.stdout is original


def test_simple_verbose_prints_durations(capsys):
    """SimpleProgressTracker verbose=True prints per-job durations."""
    t = SimpleProgressTracker(verbose=True)
    with t("Build"):
        t.job("alpha")
        time.sleep(0.01)
        t.job("beta")
        time.sleep(0.01)
    out = capsys.readouterr().out
    assert "alpha" in out
    assert "beta" in out
    assert "s" in out


def test_tty_verbose_prints_durations(capsys):
    """TtyProgressTracker verbose=True prints per-job durations."""
    t = TtyProgressTracker(verbose=True)
    with t("Build"):
        t.job("alpha")
        time.sleep(0.01)
        t.job("beta")
        time.sleep(0.01)
    out = capsys.readouterr().out
    assert "alpha" in out
    assert "beta" in out


def test_verbose_durations_on_exception(capsys):
    """verbose=True prints durations even when an exception occurs."""
    t = SimpleProgressTracker(verbose=True)
    with pytest.raises(RuntimeError):
        with t("Build"):
            t.job("alpha")
            raise RuntimeError("fail")
    out = capsys.readouterr().out
    assert "alpha" in out


def test_create_tracker_quiet():
    assert isinstance(create_tracker(quiet=True), QuietTracker)


def test_create_tracker_verbose_is_not_quiet():
    t = create_tracker(verbose=True)
    assert not isinstance(t, QuietTracker)
    assert t.verbose is True


def test_create_tracker_default():
    t = create_tracker()
    assert not isinstance(t, QuietTracker)
    assert t.verbose is False

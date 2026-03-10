import time
import pytest
from pyplanner.tracker import (
    QuietTracker, SimpleProgressTracker,
    setup_tracker, tracker,
)
from pyplanner.tracker.base import BaseTracker


def test_quiet_context_manager_noop():
    """QuietTracker context manager does nothing."""
    t = QuietTracker()
    with t("stage", total=3):
        t.job("a")
        t.job("b")


def test_quiet_no_output(capsys):
    """QuietTracker produces no stdout output."""
    t = QuietTracker()
    with t("stage"):
        t.job("a")
    assert capsys.readouterr().out == ""


def test_quiet_job_as_context_manager():
    """QuietTracker.job() works as a context manager."""
    t = QuietTracker()
    with t("stage"):
        with t.job("a"):
            pass
        with t.job("b"):
            pass


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


def test_simple_total_via_call():
    """total= in __call__ stores the value."""
    t = SimpleProgressTracker()
    with t("stage", total=5):
        assert t.job_count == 5


def test_simple_exception_propagates():
    """Exceptions propagate out of the context manager."""
    t = SimpleProgressTracker()
    with pytest.raises(RuntimeError, match="boom"), t("stage"):
        t.job("a")
        raise RuntimeError("boom")
    assert len(t.jobs) == 1


def test_simple_verbose_prints_durations(capsys):
    """verbose=True prints per-job durations."""
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


def test_verbose_durations_on_exception(capsys):
    """verbose=True prints durations even on exception."""
    t = SimpleProgressTracker(verbose=True)
    with pytest.raises(RuntimeError), t("Build"):
        t.job("alpha")
        raise RuntimeError("fail")
    out = capsys.readouterr().out
    assert "alpha" in out


def test_job_as_context_manager_records_duration():
    """with tracker.job() records duration on exit."""
    t = SimpleProgressTracker()
    with t("stage"):
        with t.job("a"):
            time.sleep(0.01)
        with t.job("b"):
            time.sleep(0.01)
    assert len(t.jobs) == 2
    assert t.jobs[0][0] == "a"
    assert t.jobs[1][0] == "b"
    assert all(d > 0 for _, d in t.jobs)


def test_job_simple_call_ignores_return():
    """job() as plain call works (return value ignored)."""
    t = SimpleProgressTracker()
    with t("stage"):
        t.job("a")
        time.sleep(0.01)
        t.job("b")
        time.sleep(0.01)
    assert len(t.jobs) == 2


@pytest.fixture(autouse=False)
def _restore_tracker():
    """Save and restore the global tracker singleton."""
    old = tracker()
    yield
    setup_tracker(old)


@pytest.mark.usefixtures("_restore_tracker")
def test_setup_tracker_quiet():
    """setup_tracker(quiet=True) installs QuietTracker."""
    setup_tracker(quiet=True)
    assert isinstance(tracker(), QuietTracker)


@pytest.mark.usefixtures("_restore_tracker")
def test_setup_tracker_verbose():
    """setup_tracker(verbose=True) installs non-quiet."""
    setup_tracker(verbose=True)
    t = tracker()
    assert isinstance(t, BaseTracker)
    assert t.verbose is True


@pytest.mark.usefixtures("_restore_tracker")
def test_setup_tracker_default():
    """setup_tracker() installs a non-quiet tracker."""
    setup_tracker()
    t = tracker()
    assert isinstance(t, BaseTracker)
    assert t.verbose is False


@pytest.mark.usefixtures("_restore_tracker")
def test_setup_tracker_custom_instance():
    """setup_tracker(instance) installs the given object."""
    custom = QuietTracker()
    setup_tracker(custom)
    assert tracker() is custom


def test_default_tracker_is_quiet():
    """Default singleton (before setup) is QuietTracker."""
    assert isinstance(tracker(), QuietTracker)


@pytest.mark.usefixtures("_restore_tracker")
def test_tracker_with_args_forwards_to_call():
    """tracker("stage") forwards to __call__ on singleton."""
    inst = SimpleProgressTracker()
    setup_tracker(inst)
    result = tracker("my stage", total=3)
    assert result is tracker()
    assert inst.stage_name == "my stage"
    assert inst.job_count == 3


@pytest.mark.usefixtures("_restore_tracker")
def test_tracker_with_args_as_context_manager(capsys):
    """with tracker("stage"): works as a context manager."""
    setup_tracker(quiet=True)
    with tracker("stage"):
        tracker().job("a")
    assert capsys.readouterr().out == ""

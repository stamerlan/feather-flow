"""Progress tracking for planner generation stages."""

import sys
from typing import overload

from .protocol import ProgressTracker
from .quiet import QuietTracker
from .simple import SimpleProgressTracker
from .tqdm import TqdmTracker

__all__ = [
    "ProgressTracker",
    "QuietTracker",
    "SimpleProgressTracker",
    "TqdmTracker",
    "setup_tracker",
    "tracker",
]

_tracker: ProgressTracker = QuietTracker()


def setup_tracker(
    instance: ProgressTracker | None = None,
    *, quiet: bool = False, verbose: bool = False,
) -> ProgressTracker:
    """Install the global tracker.

    If *instance* is given, use it directly (custom tracker). Otherwise create
    one based on the flags and environment:

    - *quiet* - ``QuietTracker`` (no output at all).
    - TTY - ``TqdmTracker``.
    - Non-TTY (pipe/file) - ``SimpleProgressTracker``.

    :param instance: Custom tracker to install.
    :param quiet: Suppress all output.
    :param verbose: Print per-job durations after each stage.
    """
    global _tracker
    if instance is not None:
        _tracker = instance
    elif quiet:
        _tracker = QuietTracker()
    elif hasattr(sys.stdout, "isatty") and sys.stdout.isatty():
        _tracker = TqdmTracker(verbose=verbose)
    else:
        _tracker = SimpleProgressTracker(verbose=verbose)
    return _tracker

@overload
def tracker() -> ProgressTracker: ...
@overload
def tracker(stage_name: str, *, total: int = 0) -> ProgressTracker: ...

def tracker(
    stage_name: str | None = None, *, total: int = 0
) -> ProgressTracker:
    """Return the global tracker instance.

    When called without arguments, returns the singleton directly. When called
    with arguments, forwards them to the tracker's ``__call__`` (which sets
    stage name / total) and returns the result. This allows::

        with tracker("Generating PDF", total=5):
            ...

    instead of the longer ``with tracker()("...", total=5):``.
    """
    if stage_name is not None:
        return _tracker(stage_name, total=total)
    return _tracker

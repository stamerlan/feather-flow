"""Progress tracking for planner generation stages.

Public API
----------
- ``ProgressTracker`` - structural protocol
- ``QuietTracker``    - silent no-op
- ``SimpleProgressTracker`` - one-line print for pipes
- ``TtyProgressTracker``    - live timer on a TTY
- ``TqdmTracker``     - tqdm-backed bar (optional dep)
- ``create_tracker``  - factory that picks the best one
"""

import sys

from .protocol import ProgressTracker
from .quiet import QuietTracker
from .simple import SimpleProgressTracker
from .tqdm import TqdmTracker
from .tty import TtyProgressTracker

__all__ = [
    "ProgressTracker",
    "QuietTracker",
    "SimpleProgressTracker",
    "TtyProgressTracker",
    "TqdmTracker",
    "create_tracker",
]


def _is_tty() -> bool:
    """Return ``True`` when stdout is a real terminal."""
    return (
        hasattr(sys.stdout, "isatty")
        and sys.stdout.isatty()
    )


def create_tracker(
    *, quiet: bool = False, verbose: bool = False,
) -> ProgressTracker:
    """Return a tracker appropriate for the environment.

    Selection logic:

    - *quiet* - ``QuietTracker`` (no output at all).
    - TTY + tqdm installed - ``TqdmTracker``.
    - TTY without tqdm - ``TtyProgressTracker``.
    - Non-TTY (pipe/file) - ``SimpleProgressTracker``.

    :param quiet: Suppress all output.
    :param verbose: Print per-job durations after each
        stage.
    """
    if quiet:
        return QuietTracker()
    if _is_tty():
        if TqdmTracker.is_available():
            return TqdmTracker(verbose=verbose)
        return TtyProgressTracker(verbose=verbose)
    return SimpleProgressTracker(verbose=verbose)

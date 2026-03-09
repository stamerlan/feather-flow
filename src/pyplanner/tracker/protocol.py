"""ProgressTracker protocol definition."""

from contextlib import AbstractContextManager
from typing import Protocol, Self


class ProgressTracker(Protocol):
    """Structural interface for all progress trackers.

    Every tracker is used as a callable context manager::

        setup_tracker(quiet=quiet, verbose=verbose)
        with tracker("Building", total=n):
            with tracker().job("step-1"):
                ...
            tracker().job("step-2")
            ...

    ``job()`` may be used as a plain call (the previous job is auto-finished
    when the next one starts or the stage exits) or as a context manager (the
    job finishes on block exit).

    Implementations do not need to inherit from this protocol; they only need to
    provide matching methods.
    """

    def __call__(self, stage_name: str, *, total: int = 0) -> Self:
        """Set the stage name and return *self*."""
        ...

    def __enter__(self) -> Self:
        """Begin tracking the stage."""
        ...

    def __exit__(
        self,
        exc_type: type | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Finish the stage and clean up resources."""
        ...

    def job(self, name: str) -> AbstractContextManager[None]:
        """Signal the start of a new job within the stage.

        Returns a context manager. Can be used as a plain call (return value
        ignored) or with ``with``.
        """
        ...

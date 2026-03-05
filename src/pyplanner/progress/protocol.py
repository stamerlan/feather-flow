"""ProgressTracker protocol definition."""

from typing import Protocol, Self


class ProgressTracker(Protocol):
    """Structural interface for all progress trackers.

    Every tracker is used as a callable context manager::

        tracker = create_tracker()
        with tracker("Building"):
            tracker.set_job_count(n)
            for item in items:
                tracker.job(item.name)
                ...

    Implementations do not need to inherit from this
    protocol; they only need to provide matching methods.
    """

    def __call__(self, stage_name: str) -> Self:
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

    def job(self, name: str) -> None:
        """Signal the start of a new job within the stage."""
        ...

    def set_job_count(self, count: int) -> None:
        """Set expected total number of jobs for the stage."""
        ...

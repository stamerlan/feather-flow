import sys
from typing import Self
from .base import BaseTracker


class SimpleProgressTracker(BaseTracker):
    """Tracker for non-interactive output (pipes, files).

    Prints the stage name once on enter. Job progress is silent. Used when
    stdout is not a TTY (e.g. piped to a file or another process).
    """

    def __enter__(self) -> Self:
        """Print ``<stage>...`` and begin tracking."""
        self.reset_stage()
        sys.stdout.write(f"{self.stage_name}...\n")
        sys.stdout.flush()
        return self

    def __exit__(
        self,
        exc_type: type | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Finish the last job and optionally print a
        verbose summary.
        """
        self.finish_current_job()
        self.active = False
        if self.verbose:
            self.print_verbose_summary()

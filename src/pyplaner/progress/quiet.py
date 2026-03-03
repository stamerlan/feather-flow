from typing import Self


class QuietTracker:
    """No-op tracker for quiet mode.

    Every method is a no-op so callers can use the same tracker interface
    without conditional checks.
    """

    def __call__(self, stage_name: str) -> Self:
        """Ignore the stage name; return *self*."""
        return self

    def __enter__(self) -> Self:
        """No-op enter."""
        return self

    def __exit__(
        self,
        exc_type: type | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """No-op exit."""
        return None

    def job(self, name: str) -> None:
        """Ignore job start."""
        return

    def set_job_count(self, count: int) -> None:
        """Ignore job count."""
        return

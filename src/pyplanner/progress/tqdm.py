import sys
from typing import Self
from tqdm.auto import tqdm
from .base import BaseTracker


class TqdmTracker(BaseTracker):
    """Progress tracker backed by *tqdm*.

    Delegates all visual output to a ``tqdm`` progress bar.
    """

    def __init__(self, *, verbose: bool = False) -> None:
        super().__init__(verbose=verbose)
        self._tqdm_bar: tqdm[None] | None = None

    def __enter__(self) -> Self:
        """Create the tqdm bar and start the refresh thread."""
        self.reset_stage()
        self._tqdm_bar = tqdm(
            total=self.job_count or None,
            desc=self.stage_name,
            bar_format="{desc}: {n_fmt}/{total_fmt} {bar} [{elapsed}]",
            dynamic_ncols=True,
            file=sys.stdout,
            leave=False,
        )
        self.start_refresh_thread()
        return self

    def __exit__(
        self,
        exc_type: type | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Stop the refresh thread and close the bar."""
        self.stop_refresh_thread()
        self.finish_current_job()
        self.active = False
        if self._tqdm_bar is not None:
            self._tqdm_bar.close()
            self._tqdm_bar = None
        if self.verbose:
            self.print_verbose_summary()

    def job(self, name: str) -> None:
        """Advance the bar by one step and update its label.

        Also syncs ``bar.total`` with ``job_count`` in case ``set_job_count``
        was called after the bar was created.
        """
        with self.lock:
            self._start_job(name)
            if self._tqdm_bar is not None:
                bar = self._tqdm_bar
                if self.job_count and bar.total != self.job_count:
                    bar.total = self.job_count
                    bar.refresh()
                bar.set_description(f"{self.stage_name}: {self.job_name}")
                bar.update(1)

    def set_job_count(self, count: int) -> None:
        """Update ``job_count`` and the bar's total."""
        super().set_job_count(count)
        if self._tqdm_bar is not None:
            self._tqdm_bar.total = count
            self._tqdm_bar.refresh()

    def refresh(self) -> None:
        """Refresh the tqdm bar (called by the background
        refresh thread under ``lock``).
        """
        if self._tqdm_bar is not None:
            self._tqdm_bar.refresh()

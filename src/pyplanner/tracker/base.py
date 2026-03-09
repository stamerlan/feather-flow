import sys
import threading
import time
from typing import Self

_REFRESH_INTERVAL = 0.1


class _JobContext:
    """Lightweight context manager returned by ``job()``.

    If used with ``with``, finishes the current job on block exit. If the return
    value is ignored, the job is auto-finished when the next ``job()`` starts or
    the stage exits.
    """

    __slots__ = ("_tracker",)

    def __init__(self, tracker: "BaseTracker") -> None:
        self._tracker = tracker

    def __enter__(self) -> None:
        return None

    def __exit__(
        self,
        exc_type: type | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> bool | None:
        with self._tracker.lock:
            self._tracker.finish_current_job()
        return None


class BaseTracker:
    """Common state and timing logic for non-quiet trackers.

    Subclasses must implement ``__enter__``, ``__exit__``, and optionally
    override ``job``. They may also override ``refresh`` to redraw their display
    on every tick of the background refresh thread.

    Usage example::

        setup_tracker(verbose=True)
        t = tracker()
        with t("Stage name", total=3):
            with t.job("step-1"):
                ...
            t.job("step-2")
            ...

    Subclasses and cooperating helpers may read or mutate these fields directly.
    The rules below describe when each field is safe to access.

    stage_name : str
        Human-readable name of the current stage. Set by ``__call__`` before the
        context manager is entered.
    job_name : str
        Name of the job currently being timed. Empty string when no job is
        active.
    job_count : int
        Expected total number of jobs. Zero means unknown.
    job_start_ts : float
        ``perf_counter`` timestamp for the current job.
    jobs : list[tuple[str, float]]
        Completed ``(name, elapsed_seconds)`` pairs. Filled by
        ``finish_current_job``.
    lock : threading.Lock
        Guards all display-related state. The background refresh thread acquires
        it before calling ``refresh``; subclasses that touch the terminal in
        ``job`` or ``__exit__`` must also hold it.
    stop_event : threading.Event
        Signalled by ``stop_refresh_thread`` to tell the background loop to
        exit.
    refresh_thread : Thread | None
        Handle to the daemon thread that calls ``refresh`` every
        ``_REFRESH_INTERVAL`` seconds. ``None`` when no thread is running.
    verbose : bool
        When ``True``, ``print_verbose_summary`` is called in ``__exit__`` to
        list per-job durations.
    """

    def __init__(self, *, verbose: bool = False) -> None:
        self.verbose: bool = verbose
        self.stage_name: str = ""
        self.job_name: str = ""
        self.job_count: int = 0
        self.job_start_ts: float = 0.0
        self.jobs: list[tuple[str, float]] = []
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.refresh_thread: threading.Thread | None = None

    def __call__(self, stage_name: str, *, total: int = 0) -> Self:
        """Set the stage name and return *self*.

        Intended for the ``with tracker()("name"):`` idiom so ``__call__`` and
        ``__enter__`` can be chained.

        :param stage_name: Human-readable stage label.
        :param total: Expected number of jobs (0 = unknown).
        """
        self.stage_name = stage_name
        self.job_count = total
        return self

    def __enter__(self) -> Self:
        """Begin tracking the stage."""
        return self

    def __exit__(
        self,
        exc_type: type | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Finish the stage and clean up resources."""
        return None

    def reset_stage(self) -> None:
        """Clear per-stage counters.

        Called at the start of ``__enter__`` in every  subclass. Preserves
        ``job_count`` set by ``__call__``.
        """
        self.jobs = []
        self.job_name = ""

    def finish_current_job(self) -> None:
        """Record elapsed time for the current job.

        No-op when no job is active (``job_name`` is empty).
        """
        if self.job_name:
            elapsed = time.perf_counter() - self.job_start_ts
            self.jobs.append((self.job_name, elapsed))
            self.job_name = ""

    def _start_job(self, name: str) -> None:
        """Finish the previous job and begin timing *name*.

        Must be called with ``lock`` held.
        """
        self.finish_current_job()
        self.job_name = name
        self.job_start_ts = time.perf_counter()

    def job(self, name: str) -> _JobContext:
        """Finish the previous job and begin timing *name*.

        Returns a ``_JobContext`` that can be used as a context manager or
        ignored.
        """
        with self.lock:
            self._start_job(name)
        return _JobContext(self)

    def start_refresh_thread(self) -> None:
        """Spawn a daemon thread that calls ``refresh``
        every ``_REFRESH_INTERVAL`` seconds.
        """
        self.stop_event.clear()
        self.refresh_thread = threading.Thread(
            target=self._refresh_loop, daemon=True,
        )
        self.refresh_thread.start()

    def stop_refresh_thread(self) -> None:
        """Signal the refresh thread to stop and wait for it to finish."""
        self.stop_event.set()
        if self.refresh_thread is not None:
            self.refresh_thread.join()
            self.refresh_thread = None

    def _refresh_loop(self) -> None:
        """Background loop: sleep then call ``refresh`` under ``lock`` until
        ``stop_event`` is set.
        """
        while not self.stop_event.wait(_REFRESH_INTERVAL):
            with self.lock:
                self.refresh()

    def refresh(self) -> None:
        """Redraw the progress display.

        Override in subclasses. Called by the background refresh thread while
        ``lock`` is held.
        """
        return

    def print_verbose_summary(self) -> None:
        """Write a per-job timing report to *stdout*.

        Typically called in ``__exit__`` when ``verbose`` is ``True``.
        """
        stream = sys.stdout
        stream.write(f"{self.stage_name}:\n")
        max_name = max(
            (len(n) for n, _ in self.jobs), default=0,
        )
        for name, duration in self.jobs:
            stream.write(
                f"  {name:<{max_name}s} : {duration:.3f}s\n"
            )
        stream.flush()

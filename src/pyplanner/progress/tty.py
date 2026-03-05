"""Elapsed-timer TTY tracker with a background refresh
thread.
"""

import shutil
import sys
import time
from typing import Any, Self, TextIO, cast

from .base import BaseTracker


class _StdoutInterceptor:
    """Wraps *stdout* so user prints don't collide with the progress line.

    Installed by ``TtyProgressTracker.__enter__`` as a replacement for
    ``sys.stdout``. Every ``write`` call first clears the progress line, writes
    the user text, then redraws the progress line when the text ends with a
    newline.

    Must hold ``tracker.lock`` during all terminal writes to avoid interleaving
    with the refresh thread.

    _original : TextIO
        The real stdout saved before the interceptor was
        installed.
    _tracker : TtyProgressTracker
        Owner tracker whose ``_clear_line`` and
        ``_draw_progress`` are called under its ``lock``.
    """

    def __init__(self, original: TextIO, tracker: "TtyProgressTracker") -> None:
        self._original = original
        self._tracker = tracker
        self.encoding: str = original.encoding
        self.errors: str | None = original.errors

    def __getattr__(self, name: str) -> Any:
        """Delegate to the original stream."""
        return getattr(self._original, name)

    def fileno(self) -> int:
        """Return the underlying file descriptor."""
        return self._original.fileno()

    def isatty(self) -> bool:
        """Delegate to the original stream."""
        return self._original.isatty()

    def write(self, text: str) -> int:
        """Clear progress, write *text*, redraw on newline.

        Acquires ``_tracker.lock`` for the entire operation so the refresh
        thread cannot interleave.
        """
        with self._tracker.lock:
            self._tracker._clear_line()
            n = self._original.write(text)
            if text.endswith("\n"):
                self._tracker._draw_progress()
        return n

    def flush(self) -> None:
        """Flush the underlying stream."""
        self._original.flush()

    def writable(self) -> bool:
        """Always writable."""
        return True


class TtyProgressTracker(BaseTracker):
    """Elapsed-timer display on a TTY, refreshed by a background thread so the
    timer updates during long steps.

    Replaces ``sys.stdout`` with a ``_StdoutInterceptor`` while active so that
    user ``print()`` calls do not collide with the single-line progress display.

    _last_line_len : int
        Length of the last progress line written. Used to pad shorter lines with
        spaces (avoiding leftover characters) and to blank the line on clear.
    _old_stdout : TextIO | None
        The original ``sys.stdout`` saved in ``__enter__`` and restored in
        ``__exit__``. ``None`` outside the context manager.
    """

    def __init__(self, *, verbose: bool = False) -> None:
        super().__init__(verbose=verbose)
        self._last_line_len: int = 0
        self._old_stdout: TextIO | None = None

    def __enter__(self) -> Self:
        """Replace stdout with an interceptor and start the refresh thread."""
        self.reset_stage()
        old_stdout = sys.stdout
        self._old_stdout = old_stdout
        sys.stdout = cast(TextIO, _StdoutInterceptor(old_stdout, self))
        self._draw_progress()
        self.start_refresh_thread()
        return self

    def __exit__(
        self,
        exc_type: type | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Stop the refresh thread, restore stdout, and print a summary or done
        message.
        """
        self.stop_refresh_thread()
        with self.lock:
            self.finish_current_job()
            self.active = False
            self._clear_line()
            if self._old_stdout is not None:
                sys.stdout = self._old_stdout
                self._old_stdout = None
        if self.verbose:
            self.print_verbose_summary()
        elif exc_type is None:
            self._print_done()

    def job(self, name: str) -> None:
        """Record a new job and redraw the progress line.

        Acquires ``lock`` because the refresh thread may be running
        concurrently.
        """
        with self.lock:
            self._start_job(name)
            self._draw_progress()

    def refresh(self) -> None:
        """Redraw the progress line (called by the refresh thread under
        ``lock``).
        """
        self._draw_progress()

    def _progress_text(self) -> str:
        """Build the single-line progress string.

        Format: ``Stage: job [idx/total] (elapsed)``.
        """
        elapsed = time.perf_counter() - self.stage_t0
        text = self.stage_name
        if self.job_name:
            text += f": {self.job_name}"
        if self.job_count:
            text += f" [{self.job_index}/{self.job_count}]"
        text += f" ({elapsed:.1f}s)"
        return text

    def _draw_progress(self) -> None:
        """Overwrite the current terminal line with fresh progress text.

        Pads with spaces to cover any leftover characters from a previous longer
        line. Writes to ``_old_stdout`` (the real stdout) to bypass the
        interceptor.
        """
        if not self.active:
            return
        text = self._progress_text()
        width = shutil.get_terminal_size().columns
        text = text[:width]
        padding = max(0, self._last_line_len - len(text))
        self._last_line_len = len(text)
        old = self._old_stdout
        stream = old if old is not None else sys.stdout
        stream.write(f"\r{text}{' ' * padding}")
        stream.flush()

    def _clear_line(self) -> None:
        """Blank the current progress line on the terminal.

        Writes spaces over the last line then returns the cursor to column zero.
        """
        old = self._old_stdout
        stream = old if old is not None else sys.stdout
        stream.write(f"\r{' ' * self._last_line_len}\r")
        stream.flush()
        self._last_line_len = 0

    def _print_done(self) -> None:
        """Print ``<stage>... done (Xs)`` on normal exit."""
        old = self._old_stdout
        stream = old if old is not None else sys.stdout
        elapsed = time.perf_counter() - self.stage_t0
        stream.write(f"\r{self.stage_name}... done ({elapsed:.1f}s)\n")
        stream.flush()

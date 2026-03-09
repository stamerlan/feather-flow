import contextlib
from contextlib import AbstractContextManager
from typing import Self


class QuietTracker:
    """No-op tracker for quiet mode.

    Every method is a no-op so callers can use the same tracker interface
    without conditional checks.
    """

    def __call__(self, stage_name: str, *, total: int = 0) -> Self:
        return self

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        return None

    def job(self, name: str) -> AbstractContextManager[None]:
        return contextlib.nullcontext()

Progress Tracking
=================

Pyplanner uses a global progress tracker to report what it is doing during PDF
generation. The tracker is a singleton that can be configured once and then
accessed from anywhere in the codebase.

Basic usage
-----------

The default tracker is silent (a :class:`~pyplanner.QuietTracker`).
Call :func:`~pyplanner.setup_tracker` to pick a visible one:

.. code-block:: python

    from pyplanner import setup_tracker, tracker

    setup_tracker()  # auto-detect: tqdm on TTY, simple otherwise

    with tracker("Generating PDF", total=3):
        with tracker().job("Step 1"):
            ...
        with tracker().job("Step 2"):
            ...
        tracker().job("Step 3")
        ...

:func:`~pyplanner.tracker` returns the global singleton. When called with
arguments it also sets the stage name and total job count, returning the tracker
so you can use it as a context manager.

``job()`` marks the start of a sub-step. It can be used as a context manager
(``with tracker().job("name"):``), or as a plain call where the previous job is
auto-finished when the next one starts or the stage exits.

Built-in trackers
-----------------

:class:`~pyplanner.QuietTracker`
    No output at all. The default.

:class:`~pyplanner.SimpleProgressTracker`
    Prints the stage name on enter. Designed for non-TTY environments
    (pipes, CI logs).

:class:`~pyplanner.TqdmTracker`
    Displays a tqdm progress bar. Chosen automatically when stdout is a TTY.

:func:`~pyplanner.setup_tracker` picks the right one based on the environment:

.. code-block:: python

    setup_tracker(quiet=True)   # QuietTracker
    setup_tracker()             # TqdmTracker on TTY, else Simple
    setup_tracker(verbose=True) # same, but with per-job durations

Writing a custom tracker
-------------------------

The :class:`~pyplanner.ProgressTracker` protocol defines the interface. Your
class does not need to inherit from it - it only needs to provide matching
methods:

.. code-block:: python

    import logging
    from contextlib import contextmanager

    log = logging.getLogger(__name__)

    class LoggingTracker:
        """Report progress via the logging module."""

        def __call__(self, stage_name, *, total=0):
            self._stage = stage_name
            return self

        def __enter__(self):
            log.info("Starting: %s", self._stage)
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            log.info("Finished: %s", self._stage)

        @contextmanager
        def job(self, name):
            log.debug("  Job: %s", name)
            yield

Install it with :func:`~pyplanner.setup_tracker`:

.. code-block:: python

    from pyplanner import setup_tracker

    setup_tracker(LoggingTracker())

All subsequent pyplanner operations will use your tracker.

Why a singleton?
----------------

An earlier design passed the tracker as a parameter through ``Planner.pdf()``,
``optimize()`` and every helper function. The parameter-passing approach had
several problems:

- Every function signature gained a ``tracker`` parameter that most callers left
  as ``None``.
- Adding progress tracking to a new function required changing its signature and
  all call sites.
- The tracker is a cross-cutting concern - it does not affect the return value
  or control flow.

The singleton is configured once at startup with ``setup_tracker()`` and then
accessed from anywhere. This keeps internal APIs clean and makes it easy to add
progress reporting to new functions without signature changes.

API reference
-------------

.. autofunction:: pyplanner.setup_tracker

.. autofunction:: pyplanner.tracker

.. autoclass:: pyplanner.ProgressTracker
   :members:

.. autoclass:: pyplanner.QuietTracker
   :members:

.. autoclass:: pyplanner.SimpleProgressTracker
   :members:

.. autoclass:: pyplanner.TqdmTracker
   :members:

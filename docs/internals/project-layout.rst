Project Layout
==============

Source layout
-------------

The project uses the ``src/`` layout recommended by the Python Packaging
Authority. The package source lives under ``src/pyplanner/`` and is never
importable directly from the repository root - you must install the package
first (``pip install -e .``). This prevents accidental imports of the
development tree in tests or scripts and ensures the installed package is always
what gets tested.

::

    feather-flow/
      pyproject.toml          Build metadata and tool config
      README.rst              Project README (included in Sphinx docs)
      src/
        pyplanner/
          __init__.py          Public API exports
          __main__.py          CLI entry point
          calendar.py          Calendar, Year, Month, Day
          dayinfo.py           DayInfo, DayInfoProvider
          lang.py              Lang registry
          liveserver.py        watch() live-reload server
          params.py            Params XML schema and -D overrides
          pdfbookmarks.py      PDF outline/bookmarks
          pdfopt.py            PDF optimization (image dedup)
          planner.py           Planner (Jinja2 + Playwright)
          weekday.py           WeekDay and country rules
          providers/
            __init__.py        Re-exports built-in providers
            isdayoff.py        IsDayOffProvider (RU, BY, KZ, UZ, GE)
            nagerdate.py       NagerDateProvider (100+ countries)
          tracker/
            __init__.py        setup_tracker(), tracker() singleton
            protocol.py        ProgressTracker protocol
            base.py            BaseTracker with refresh thread
            simple.py          SimpleProgressTracker (non-TTY)
            tqdm.py            TqdmTracker (TTY progress bar)
            quiet.py           QuietTracker (no-op)
      tests/                   One test file per source module
      planners/                Self-contained planner templates
      docs/                    Sphinx documentation

Self-contained planner directories
-----------------------------------

Each planner lives in its own directory under ``planners/`` with the template,
``params.xml`` and an ``assets/`` folder::

    planners/ff-2026/
      ff-2026.html
      params.xml
      assets/
        ff-2026.css
        cover.png
        ...

Earlier versions kept templates and assets in separate top-level directories.
This made it hard to copy or share a planner as a unit. Moving to self-contained
directories means you can zip a folder and hand it to someone - everything
needed to render the planner is inside. In watch mode whole planner directory is
watched for changes and the HTML is regenerated automatically.

The trade-off is that asset paths in templates must use
``{{ base }}/assets/...`` instead of relative paths. The ``base`` variable is
injected at render time and points to the template directory.

Dependencies
------------

All runtime dependencies (jinja2, livereload, pikepdf, playwright, tqdm) are
listed under ``[project.dependencies]`` in ``pyproject.toml``, not as optional
extras.

An earlier version split them into ``[project.optional-dependencies]`` groups
(``full``, ``pdf``, etc.). This caused silent degradation when users forgot to
install the right extra - ``import pikepdf`` would fail at runtime with a
confusing ``ModuleNotFoundError`` deep inside a PDF generation call.

Making everything mandatory means ``pip install pyplanner`` gives you a fully
working package. The install size increase is acceptable because all
dependencies are needed for the primary use case (PDF generation).

Development tools (pytest, ruff, mypy, Sphinx, pre-commit) live in the ``[dev]``
optional extra because they are needed by package developers only.

Module dependency graph
-----------------------

The modules have a clear dependency hierarchy. Leaf modules at the
bottom have no internal dependencies; higher modules compose them.

::

    __main__
      |
      +-- Planner -----+-- Calendar --+-- DayInfoProvider
      |                |              |     (+ DayInfo)
      |                |              +-- Lang
      |                |              +-- WeekDay
      |                |
      |                +-- pdfbookmarks
      |                +-- tracker
      |
      +-- Params
      +-- pdfopt
      +-- liveserver --+-- Planner
                       +-- Params

``__main__`` is the CLI orchestrator. It builds a :class:`~pyplanner.Calendar`,
a :class:`~pyplanner.Planner` and wires them together based on command-line
arguments.

``planner`` depends on ``calendar``, ``lang`` and ``pdfbookmarks`` but does
*not* depend on ``pdfopt`` - optimization is applied by the caller (``__main__``
or user code), keeping the rendering path clean. PDF bookmarks are generated
together with the PDF, because they are extracted from the HTML page IDs.

``liveserver`` imports :class:`~pyplanner.Planner` and
:class:`~pyplanner.Params` because it rebuilds the HTML on file changes and
needs to re-parse ``params.xml`` each time.

The ``tracker`` sub-package is used throughout but has no dependencies on the
rest of pyplanner.

What each module does
---------------------

**calendar.py**
    Wraps the stdlib :mod:`calendar` module to build :class:`~pyplanner.Year`,
    :class:`~pyplanner.Month` and :class:`~pyplanner.Day` objects enriched with
    localized names and optional holiday data from a
    :class:`~pyplanner.DayInfoProvider`.

**dayinfo.py**
    Defines the :class:`~pyplanner.DayInfo` dataclass and the
    :class:`~pyplanner.DayInfoProvider` abstract base class. Also provides the
    plugin loader that discovers providers by duck typing from arbitrary
    modules.

**weekday.py**
    :class:`~pyplanner.WeekDay` carries a day's localized name, abbreviation and
    off-day flag. Country lookup tables determine first-weekday and weekend
    rules for 100+ countries.

**lang.py**
    :class:`~pyplanner.Lang` is a frozen dataclass with a static registry.
    Built-in languages (en, ru, kr) are registered at import time. Alias support
    (``ko`` -> ``kr``) avoids duplicating data.

**params.py**
    :class:`~pyplanner.Params` loads a typed XML schema, validates names and
    types, and produces a :class:`~types.SimpleNamespace` tree. ``-D KEY=VALUE``
    overrides walk the dot-path and set values with type coercion.

**planner.py**
    :class:`~pyplanner.Planner` sets up a Jinja2 environment with custom
    delimiters (``%%`` / ``##``), renders templates with ``base``, ``calendar``,
    ``lang`` and ``params`` as context, and optionally prints to PDF via
    Playwright. PDF bookmarks are extracted from ``.page`` element IDs.

**pdfopt.py**
    Post-processing for Chromium-generated PDFs. Deduplicates Image XObjects by
    SHA-256 hash, strips obsolete ``/ProcSet`` arrays, deduplicates Form
    XObjects, and recompresses with object streams.

**pdfbookmarks.py**
    Inserts PDF outline entries via pikepdf. Supports multi-level bookmarks by
    specifying a parent path.

**liveserver.py**
    Wraps the livereload library to watch the template directory and rebuild
    HTML on changes. Imports livereload lazily to avoid its
    ``logging.basicConfig()`` side effect.

**providers/isdayoff.py**
    Fetches a binary workday/off-day string from isdayoff.ru for Russia,
    Belarus, Kazakhstan, Uzbekistan and Georgia.

**providers/nagerdate.py**
    Fetches public holiday JSON from the Nager.Date API for 100+ countries.

**tracker/**
    A :class:`~pyplanner.ProgressTracker` protocol with three implementations
    (quiet, simple, tqdm) and a module-level singleton accessed via
    :func:`~pyplanner.tracker`.

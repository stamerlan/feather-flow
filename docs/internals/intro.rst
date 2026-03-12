Internals
=========

This section is for developers who want to work on the pyplanner package
itself - fix bugs, add features, improve tests or update the documentation. It
covers the development environment, source layout, test suite, linting and CI
pipelines.

If you are looking for how to *use* pyplanner in your own project, see the
:doc:`/developer-guide/intro`.

Clone the repository::

    git clone https://github.com/stamerlan/feather-flow.git
    cd feather-flow

Create a virtual environment and install the package in editable mode with
development extras:

On **Linux / macOS**::

    python -m venv .venv
    source .venv/bin/activate
    pip install -e .[dev]

On **Windows**::

    python -m venv .venv
    .venv\Scripts\activate
    pip install -e .[dev]

The ``[dev]`` extra pulls in everything you need: pytest, ruff, mypy,
pre-commit, Sphinx and their dependencies.

Install the Playwright browser binary (needed for PDF tests and generation)::

    playwright install chromium

Optionnally you may install pre-commit hooks so they run automatically before
each commit::

    pre-commit install

Verify the setup by running the test suite::

    pytest

You should see all tests pass with no warnings.

.. toctree::
   :maxdepth: 1

   project-layout
   testing
   linting-and-ci
   building-docs

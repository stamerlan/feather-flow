Linting and CI
==============

Code quality tools
------------------

Ruff
^^^^

`Ruff <https://docs.astral.sh/ruff/>`_ is the linter and formatter. It is
configured in ``pyproject.toml``:

.. code-block:: toml

    [tool.ruff]
    target-version = "py312"
    line-length = 80
    src = ["src"]

    [tool.ruff.lint]
    select = [
        "B",    # flake8-bugbear
        "E",    # pycodestyle errors
        "F",    # pyflakes
        "N",    # pep8-naming
        "PTH",  # flake8-use-pathlib
        "RUF",  # Ruff-specific rules
        "S",    # flake8-bandit (security)
        "SIM",  # flake8-simplify
        "UP",   # pyupgrade
        "W",    # pycodestyle warnings
    ]

The rule set was chosen to catch common bugs (``B``), security issues (``S``),
outdated patterns (``UP``) and unnecessary complexity (``SIM``) without being
overly noisy. Per-file ignores are applied where rules conflict with intentional
patterns:

- ``lang.py`` - Cyrillic characters trigger ``RUF001``.
- ``pdfopt.py`` - broad ``except: pass`` is intentional for best-effort
  optimization (``S110``, ``S112``).
- ``providers/*`` - ``urlopen`` calls are expected (``S310``).
- ``tests/*`` - ``assert`` is the standard way to write checks (``S101``).
- ``test_pdfopt.py`` - late imports after ``pytest.importorskip`` (``E402``).

Run ruff manually::

    ruff check .

Mypy
^^^^

`Mypy <https://mypy-lang.org/>`_ runs in strict mode:

.. code-block:: toml

    [tool.mypy]
    python_version = "3.12"
    strict = true

Two overrides relax strictness where full typing is impractical:

- ``livereload.*`` - no type stubs available (``ignore_missing_imports``).
- ``tests.*`` - fixtures and mocks are hard to type fully
  (``disallow_untyped_defs = false``).

Run mypy manually::

    mypy src/

Pre-commit hooks
----------------

The ``.pre-commit-config.yaml`` runs three hook sets before every commit:

1. **pre-commit-hooks** (v6.0.0) - trailing whitespace, end-of-file fixer,
   YAML check.
2. **ruff** (v0.15.5) - linting.
3. **mypy** (v1.19.0) - type checking with ``types-tqdm`` stubs.

Install the hooks (one-time setup)::

    pre-commit install

Run all hooks against every file manually::

    pre-commit run --all-files

CI pipelines
------------

Three GitHub Actions workflows automate quality checks and artifact generation.

test.yml
^^^^^^^^

Triggered on every push to ``main`` and every pull request.

**lint** job:

1. Install ``pip install -e .[dev]``
2. ``ruff check .``
3. ``mypy src/``
4. Generate and upload a lint badge.

**test** job:

1. Install ``pip install -e .[dev]``
2. ``pytest --cov --cov-report=term --cov-report=xml:coverage.xml``
3. Generate and upload a coverage badge.

**publish** job (main branch only):

Pushes the lint and coverage badge SVGs to the ``_artifacts`` orphan branch so
they are available at stable raw URLs for the README badges.

build-pdf.yml
^^^^^^^^^^^^^

Triggered on every push to ``main`` and every pull request. Builds PDFs for
multiple countries using a matrix strategy (``pl``, ``by``, ``us``, ``kr``). On
the main branch, the resulting PDFs are pushed to the ``_artifacts`` branch.

build-sphinx-docs.yml
^^^^^^^^^^^^^^^^^^^^^

Triggered on push to ``main``. Builds the Sphinx HTML documentation and deploys
it to GitHub Pages.

The ``_artifacts`` branch
-------------------------

Instead of GitHub Releases with moving tags, badge SVGs and pre-built PDFs are
pushed to an orphan branch called ``_artifacts``. This gives stable raw URLs
like::

    https://github.com/stamerlan/feather-flow/raw/_artifacts/coverage-badge.svg

The release-based approach had problems:

- Moving tags (e.g. ``latest``) cause confusion with ``git fetch``.
- Release assets require authentication for private repos.
- The release page becomes cluttered with auto-generated entries.

The ``_artifacts`` branch provides stable raw URLs, works without
authentication, and keeps the release history clean for actual version releases.

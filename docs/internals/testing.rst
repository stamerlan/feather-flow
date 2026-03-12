Testing
=======

Running tests
-------------

Run the full test suite with pytest::

    pytest

Run with coverage reporting::

    pytest --cov --cov-report=term

Generate an XML coverage report (used by CI)::

    pytest --cov --cov-report=term --cov-report=xml:coverage.xml

Run a single test file::

    pytest tests/test_calendar.py

Run a single test by name::

    pytest tests/test_calendar.py -k test_year_months_count

Coverage configuration lives in ``.coveragerc``:

.. code-block:: ini

    [run]
    branch = True
    source = src/pyplanner

    [report]
    exclude_also =
        def __repr__
        raise AssertionError
        raise NotImplementedError
        if __name__ == .__main__.:
        if TYPE_CHECKING:

Test organization
-----------------

There is one test file per source module:

==========================  ============================
Test file                   Module under test
==========================  ============================
``test_calendar.py``        ``calendar.py``
``test_dayinfo.py``         ``dayinfo.py``
``test_lang.py``            ``lang.py``
``test_liveserver.py``      ``liveserver.py``
``test_main.py``            ``__main__.py``
``test_params.py``          ``params.py``
``test_pdfopt.py``          ``pdfopt.py``
``test_planner.py``         ``planner.py``
``test_providers.py``       ``providers/``
``test_tracker.py``         ``tracker/``
``test_weekday.py``         ``weekday.py``
==========================  ============================

There is no shared ``conftest.py``. Fixtures are defined locally in each test
file, close to the tests that use them. This keeps each file self-contained and
easy to read in isolation.

All tests are unit tests
------------------------

Every test runs without network access or a browser. External dependencies are
patched:

- **HTTP requests** (providers) are mocked with
  ``unittest.mock.patch("urllib.request.urlopen")``.
- **Livereload server** is mocked so no real HTTP server is started.
- **Playwright/Chromium** is not invoked in tests. The ``Planner`` tests only
  exercise ``html()`` rendering. PDF generation is tested at the CLI level in
  ``test_main.py`` using template stubs that do not require a browser.
- **pikepdf** is used directly in ``test_pdfopt.py`` with in-memory PDFs - no
  file I/O beyond ``BytesIO``.

Writing new tests
-----------------

When adding a new module, create a corresponding ``tests/test_<module>.py``
file. Follow the existing conventions:

1. **One file per module.** If the module is in a sub-package
   (e.g. ``providers/nagerdate.py``), tests go in ``test_providers.py``
   alongside tests for other providers.

2. **Local fixtures.** Define fixtures in the test file, not in a shared
   conftest. Use ``tmp_path`` (pytest built-in) for temporary files.

3. **Mock external calls.** Never make real network requests or launch a browser
   in tests.

4. **Descriptive docstrings.** Each test function should have a one-line
   docstring explaining what it verifies.

Example test:

.. code-block:: python

    import pytest
    from pyplanner import Calendar

    def test_year_has_twelve_months():
        """Calendar.year() returns a Year with exactly 12 months."""
        cal = Calendar()
        year = cal.year(2026)
        assert len(year.months) == 12

    def test_leap_year():
        """Year.isleap is True for leap years."""
        cal = Calendar()
        assert cal.year(2024).isleap is True
        assert cal.year(2025).isleap is False

    @pytest.fixture()
    def russian_calendar():
        return Calendar(lang="ru")

    def test_russian_month_names(russian_calendar):
        """Russian calendar uses Cyrillic month names."""
        year = russian_calendar.year(2026)
        assert year.months[0].name == "\u042f\u043d\u0432\u0430\u0440\u044c"

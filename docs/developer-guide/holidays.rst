Holidays and Day Info
=====================

Pyplanner separates the calendar structure from the holiday data. Any class that
implements the right interface can supply per-day metadata (public holidays,
transferred workdays, etc.) to the calendar model.

DayInfo
-------

:class:`~pyplanner.DayInfo` is a simple dataclass that carries metadata about a
single day:

.. code-block:: python

    from pyplanner import DayInfo

    info = DayInfo(
        is_off_day=True,
        name="Christmas Day",
        local_name="Boze Narodzenie",
        launch_year=None,
        holiday_types=("Public",),
    )

Every field defaults to ``None``, meaning "no data - fall back to default
logic". When ``is_off_day`` is ``None``, the calendar uses the weekday's default
weekend rule instead.

Built-in providers
------------------

Pyplanner ships two providers that fetch holiday data from free public APIs.

NagerDateProvider
^^^^^^^^^^^^^^^^^

Covers 100+ countries via the `Nager.Date <https://date.nager.at>`_ API. Returns
public holidays with names and types. Free, no API key required.

.. code-block:: python

    from pyplanner import Calendar
    from pyplanner.providers import NagerDateProvider

    provider = NagerDateProvider("PL")
    cal = Calendar(firstweekday=0, provider=provider)
    year = cal.year(2026)

    for day in year.days():
        if day.name:
            print(f"{day.id}  {day.name}")

IsDayOffProvider
^^^^^^^^^^^^^^^^

Covers Russia, Belarus, Kazakhstan, Uzbekistan and Georgia via the
`isdayoff.ru <https://isdayoff.ru>`_ API. Returns a binary workday/off-day flag
for every day of the year including transferred workdays. Free, no API key
required.

.. code-block:: python

    from pyplanner.providers import IsDayOffProvider

    provider = IsDayOffProvider("RU")
    cal = Calendar(firstweekday=0, provider=provider)
    year = cal.year(2026)

    workdays = sum(1 for d in year.days() if not d.is_off_day)
    print(f"Workdays in 2026 (Russia): {workdays}")

Both providers issue a warning and return ``None`` when the network request
fails. The calendar then falls back to weekday-based weekend rules - no
holidays, but no crash either.

Writing a custom provider
-------------------------

A provider is any class with two methods:

1. ``__init__(self, country_code: str)`` - raise ``ValueError`` if the country
   is not supported.
2. ``fetch_day_info(self, year: int) -> dict[str, DayInfo] | None`` - return a
    mapping of ``YYYY-MM-DD`` strings to :class:`~pyplanner.DayInfo` instances,
    or ``None`` on failure.

The provider does *not* need to inherit from
:class:`~pyplanner.DayInfoProvider`. Pyplanner discovers providers by duck
typing at runtime: if it has ``fetch_day_info``, it qualifies.

Duck typing was chosen over a formal plugin registry (entry points, abstract
base class enforcement) because:

1. It allows standalone single-file providers with zero dependencies on
   pyplanner.
2. It avoids the complexity of setuptools entry points for a project that does
   not publish to PyPI yet.
3. Duck typing is idiomatic Python and easy to understand.

Here is a minimal standalone provider (e.g. ``my_holidays.py``):

.. code-block:: python

    from dataclasses import dataclass

    @dataclass
    class DayInfo:
        is_off_day: bool | None = None
        name: str | None = None
        local_name: str | None = None
        launch_year: int | None = None
        holiday_types: tuple[str, ...] | None = None

    class CompanyHolidayProvider:
        """Mark company-specific days off."""

        def __init__(self, country_code: str) -> None:
            if country_code.upper() != "US":
                raise ValueError(f"Unsupported: {country_code!r}")

        def fetch_day_info(self, year: int):
            return {
                f"{year}-07-04": DayInfo(
                    is_off_day=True,
                    name="Independence Day",
                ),
                f"{year}-12-25": DayInfo(
                    is_off_day=True,
                    name="Christmas Day",
                ),
            }

Use it from the CLI::

    pyplanner planners/demo --provider my_holidays --country us

Or from code:

.. code-block:: python

    from pyplanner import Calendar
    from my_holidays import CompanyHolidayProvider

    cal = Calendar(
        firstweekday=0,
        provider=CompanyHolidayProvider("US")
    )

Loading providers dynamically
-----------------------------

:meth:`DayInfoProvider.load() <pyplanner.DayInfoProvider.load>` imports a module
by dotted name (or file path) and returns every provider class found in it. This
is how the CLI ``--provider`` flag works:

.. code-block:: python

    from pyplanner import DayInfoProvider

    classes = DayInfoProvider.load("pyplanner.providers")
    for cls in classes:
        print(cls.__name__)
    # IsDayOffProvider
    # NagerDateProvider

    # Load from a file path:
    classes = DayInfoProvider.load("my_holidays.py")

API reference
-------------

.. autoclass:: pyplanner.DayInfo
   :members:

.. autoclass:: pyplanner.DayInfoProvider
   :members: load, is_provider_class, fetch_day_info

.. autoclass:: pyplanner.providers.NagerDateProvider
   :members: fetch_day_info

.. autoclass:: pyplanner.providers.IsDayOffProvider
   :members: fetch_day_info

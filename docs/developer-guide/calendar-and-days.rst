Calendar and Days
=================

The calendar model is the core data structure that planner templates consume. It
is built around four classes - :class:`~pyplanner.Calendar`,
:class:`~pyplanner.Year`, :class:`~pyplanner.Month` and
:class:`~pyplanner.Day` - plus :class:`~pyplanner.WeekDay` for weekday metadata
and :class:`~pyplanner.lang.Lang` for localization.

Building a calendar
-------------------

Create a :class:`~pyplanner.Calendar` and call its
:meth:`~pyplanner.Calendar.year` method:

.. code-block:: python

    from pyplanner import Calendar

    cal = Calendar()           # Monday start, English names
    year = cal.year(2026)

    print(year)                # 2026
    print(year.isleap)         # False
    print(len(year.months))    # 12

The ``firstweekday`` parameter controls which day starts the week (0 = Monday,
6 = Sunday). It affects the week-aligned table layout in every month:

.. code-block:: python

    cal_us = Calendar(firstweekday=6)   # Sunday start
    cal_sa = Calendar(firstweekday=5)   # Saturday start

Months and days
---------------

Each :class:`~pyplanner.Year` contains twelve :class:`~pyplanner.Month` objects:

.. code-block:: python

    january = year.months[0]

    print(january.name)        # January
    print(january.short_name)  # Jan
    print(january.value)       # 1
    print(january.id)          # 2026-01

A month exposes its days in two ways:

``month.days``
    A flat list of :class:`~pyplanner.Day` objects, one per calendar day (1st
    through 28th/29th/30th/31st).

``month.table``
    A week-aligned grid where each row is a 7-element list. Cells contain a
    :class:`~pyplanner.Day` or ``None`` for padding days outside the month. This
    is the structure templates use to render calendar grids:

.. code-block:: python

    for week in january.table:
        row = []
        for cell in week:
            if cell is None:
                row.append("  ")
            else:
                row.append(f"{cell.value:2d}")
        print(" ".join(row))

Day properties
--------------

Each :class:`~pyplanner.Day` carries:

.. code-block:: python

    day = january.days[0]

    day.value          # 1
    day.id             # "2026-01-01"
    day.weekday        # WeekDay instance
    day.is_off_day     # True if weekend or holiday

    # Holiday metadata (populated by a DayInfoProvider):
    day.name           # "New Year's Day" or None
    day.local_name     # localized holiday name or None
    day.launch_year    # year the holiday was established or None
    day.holiday_types  # ("Public",) or None

The ``is_off_day`` property first checks whether a
:class:`~pyplanner.dayinfo.DayInfoProvider` explicitly marked the day, then
falls back to the weekday's default weekend rule.

Iterating all days in a year
----------------------------

:meth:`Year.days() <pyplanner.Year.days>` is a generator that yields every day
across all twelve months:

.. code-block:: python

    off_count = sum(1 for d in year.days() if d.is_off_day)
    print(f"{off_count} off-days in {year}")

Weekdays
--------

:class:`~pyplanner.WeekDay` objects are available on every
:class:`~pyplanner.Day` and on the calendar itself:

.. code-block:: python

    cal = Calendar(firstweekday=0, country="us")

    for wd in cal.weekdays:
        print(wd.name, wd.short_name, wd.letter, wd.is_off_day)

``cal.weekdays`` is rotated so the first element matches ``firstweekday``.
Templates use it to render weekday headers in calendar grids.

Country-aware weekdays
^^^^^^^^^^^^^^^^^^^^^^

When a ``country`` is provided, the weekend rule is determined automatically.
Most countries use Saturday-Sunday, but some use Friday-Saturday (e.g. ``AE``,
``SA``) or Friday only (``MR``):

.. code-block:: python

    from pyplanner import WeekDay

    # What day does the week start on in the US?
    print(WeekDay.first_weekday_for_country("us"))  # 6 (Sunday)

    # Create a weekday with UAE weekend rules
    friday = WeekDay.create(4, country="ae")
    print(friday.is_off_day)  # True (Friday is off in UAE)

Localization
------------

Month and weekday names are localized through the :class:`~pyplanner.lang.Lang`
registry. ``Lang`` is a frozen dataclass with a static registry. Languages are
registered at import time by calling ``Lang.add()``. An alias map (``ko`` ->
``kr``) lets users pass either code without duplicating the entire translation
dataset.

The registry pattern was chosen over file-based translations (JSON/YAML) because
the data is small (7 weekday names + 12 month names per language), a frozen
dataclass with ``__post_init__`` validation catches errors at import time rather
than at render time, and there is no file I/O or parsing overhead.

Built-in languages are ``en``, ``ru`` and ``kr``.

.. code-block:: python

    cal_ru = Calendar(lang="ru")
    year_ru = cal_ru.year(2026)
    print(year_ru.months[0].name)  # Январь

You can register a custom language:

.. code-block:: python

    from pyplanner.lang import Lang

    Lang.add(Lang(
        code="de",
        weekday_names=(
            "Montag", "Dienstag", "Mittwoch", "Donnerstag",
            "Freitag", "Samstag", "Sonntag",
        ),
        weekday_short_names=("Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"),
        weekday_letters=("M", "D", "M", "D", "F", "S", "S"),
        month_names=(
            "Januar", "Februar", "Maerz", "April", "Mai",
            "Juni", "Juli", "August", "September", "Oktober",
            "November", "Dezember",
        ),
        month_short_names=(
            "Jan", "Feb", "Mae", "Apr", "Mai", "Jun",
            "Jul", "Aug", "Sep", "Okt", "Nov", "Dez",
        ),
    ))

    cal_de = Calendar(lang="de")
    print(cal_de.year(2026).months[0].name)  # Januar

API reference
-------------

.. autoclass:: pyplanner.Calendar
   :members: year

.. autoclass:: pyplanner.Year
   :members: isleap, days

.. autoclass:: pyplanner.Month
   :members:

.. autoclass:: pyplanner.Day
   :members: is_off_day, name, local_name, launch_year,
             holiday_types

.. autoclass:: pyplanner.WeekDay
   :members: first_weekday_for_country, create, parse_weekday,
             all_weekdays

.. autoclass:: pyplanner.lang.Lang
   :members: add, get, supported

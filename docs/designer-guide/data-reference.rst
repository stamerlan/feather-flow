Data Reference
==============

Every template receives a small set of objects from pyplaner. This page is a
complete reference of those objects, their properties and the values they
produce. Keep it open while you design - it answers "what can I put inside
``{{ }}``?".

**Key topics**

* The variables injected into every template (``calendar``, ``planner_head``
  and ``lang``).
* Year, Month, Day, WeekDay objects and their properties.
* The ``month.table`` grid explained visually.
* String representation shortcuts.
* The ``loop`` variable inside ``for`` blocks.


Injected variables
------------------

pyplaner passes these variables to your template:

.. list-table::
   :header-rows: 1
   :widths: 20 20 55

   * - Name
     - Type
     - Description
   * - ``calendar``
     - Calendar
     - Entry point for all calendar data. Use it to build a Year object and to
       access weekday names.
   * - ``planner_head``
     - string
     - HTML to inject in ``<head>``. Empty for HTML output, contains a
       ``<base>`` tag for PDF output. Always include it.
   * - ``lang``
     - string
     - The active display language code (e.g. ``"en"``, ``"ru"``, ``"kr"``),
       set by ``--lang``. Use it to apply language-specific CSS such as font
       families, font sizes or layout adjustments.


Calendar
--------

The ``calendar`` object itself has two things you will use:

.. list-table::
   :header-rows: 1
   :widths: 30 15 50

   * - Expression
     - Type
     - Description
   * - ``calendar.year(2026)``
     - Year
     - Build a Year object for the given year number.
   * - ``calendar.weekdays``
     - tuple
     - Seven WeekDay objects starting from the configured first day of the week.
       Defaults to Monday through Sunday; changes when ``--first-weekday`` or
       ``--country`` is used.
   * - ``calendar.firstweekday``
     - int
     - The first day of the week as a number (0 = Monday ... 6 = Sunday).
   * - ``calendar.lang``
     - string
     - The active display language code (same value as the top-level ``lang``
       variable).

``calendar.weekdays`` example (default, Monday start):

**Template:**

.. code-block:: html+jinja

   %% for wd in calendar.weekdays
   {{ wd.name }}
   %% endfor

**Output:**

.. code-block:: text

   Monday
   Tuesday
   Wednesday
   Thursday
   Friday
   Saturday
   Sunday

When ``--first-weekday sunday`` is used, the same loop outputs:

.. code-block:: text

   Sunday
   Monday
   Tuesday
   Wednesday
   Thursday
   Friday
   Saturday


Year
----

Returned by ``calendar.year()``.

.. list-table::
   :header-rows: 1
   :widths: 25 10 20 40

   * - Property
     - Type
     - Example
     - Description
   * - ``value``
     - int
     - ``2026``
     - The year number.
   * - ``months``
     - list
     - (12 Month objects)
     - All months, January through December.
   * - ``id``
     - string
     - ``"2026"``
     - Identifier string. Useful for HTML ``id`` attributes.
   * - ``isleap``
     - bool
     - ``false``
     - Whether the year is a leap year.
   * - ``days()``
     - iterator
     - (365 or 366 Day objects)
     - Every day in the year, in order.

**String representation:** ``{{ year }}`` outputs the year number, for example
``2026``.


Month
-----

Each item in ``year.months``.

.. list-table::
   :header-rows: 1
   :widths: 25 10 20 40

   * - Property
     - Type
     - Example
     - Description
   * - ``value``
     - int
     - ``1``
     - Month number (1 = January, 12 = December).
   * - ``name``
     - string
     - ``"January"``
     - Full month name (translated when ``--lang`` is used).
   * - ``short_name``
     - string
     - ``"Jan"``
     - Abbreviated month name (translated when ``--lang`` is used).
   * - ``days``
     - list
     - (28-31 Day objects)
     - Every day in the month, in order.
   * - ``table``
     - list of lists
     - (see below)
     - Calendar grid for rendering tables.
   * - ``id``
     - string
     - ``"2026-01"``
     - Identifier in ``YYYY-MM`` format.

**String representation:** ``{{ month }}`` outputs the month name, for example
``January``.


Understanding ``month.table``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``month.table`` is a list of weeks. Each week is a list of seven slots - one per
weekday, ordered to match ``calendar.weekdays``. A slot contains a Day object or
``None`` if that weekday falls outside the month.

The column order depends on the configured first day of the week.

January 2026 starts on Thursday. With the default Monday start the table looks
like this::

    Mon   Tue   Wed   Thu   Fri   Sat   Sun
    ----  ----  ----  ----  ----  ----  ----
    None  None  None  1     2     3     4
    5     6     7     8     9     10    11
    12    13    14    15    16    17    18
    19    20    21    22    23    24    25
    26    27    28    29    30    31    None


In your template you loop over weeks (rows) and then over days (cells). Check
for ``None`` before printing:

.. code-block:: html+jinja

   %% for week in month.table
   <tr>
     %% for day in week
     %% if day is not none
     <td>{{ day }}</td>
     %% else
     <td></td>
     %% endif
     %% endfor
   </tr>
   %% endfor


Day
---

Each item in ``month.days`` or in the cells of ``month.table``.

.. list-table::
   :header-rows: 1
   :widths: 25 10 25 35

   * - Property
     - Type
     - Example
     - Description
   * - ``value``
     - int
     - ``15``
     - Day of month number.
   * - ``weekday``
     - WeekDay
     - (WeekDay object)
     - The weekday this day falls on.
   * - ``id``
     - string
     - ``"2026-01-15"``
     - Identifier in ``YYYY-MM-DD`` format. Use for HTML ``id``
       attributes and ``href="#..."`` links.
   * - ``is_off_day``
     - bool
     - ``true``
     - Whether this is a day off (weekend or public holiday).

**String representation:** ``{{ day }}`` outputs the day number, for example
``15``.


Linking between pages
~~~~~~~~~~~~~~~~~~~~~

Every Day, Month and Year has an ``id`` property that makes a good HTML anchor.
Set it as the ``id`` of a ``.page`` div, then link to it with ``#``:

**Template:**

.. code-block:: html+jinja

   ## Create a page with an anchor
   <div class="page" id="{{ day.id }}">
     ...
   </div>

   ## Link to that page from elsewhere
   <a href="#{{ day.id }}">{{ day }}</a>

**Output:**

.. code-block:: html

   <div class="page" id="2026-01-15">
     ...
   </div>

   <a href="#2026-01-15">15</a>


WeekDay
-------

Each item in ``calendar.weekdays`` or accessed through ``day.weekday``.

.. list-table::
   :header-rows: 1
   :widths: 25 10 25 35

   * - Property
     - Type
     - Example
     - Description
   * - ``value``
     - int
     - ``0``
     - Weekday number (starting from zero).
   * - ``name``
     - string
     - ``"Monday"``
     - Full weekday name (translated when ``--lang`` is used).
   * - ``short_name``
     - string
     - ``"Mon"``
     - Abbreviated weekday name (translated when ``--lang`` is used).
   * - ``letter``
     - string
     - ``"M"``
     - Single-letter weekday label (translated when ``--lang`` is used).
       Suitable for compact calendar grids.
   * - ``is_off_day``
     - bool
     - ``false``
     - Default off-day flag. Saturday and Sunday are ``true``, the rest are
       ``false``.

**String representation:** ``{{ weekday }}`` outputs the weekday name, for
example ``Monday``.

Common patterns:

.. list-table::
   :header-rows: 1
   :widths: 40 25

   * - Expression
     - Output
   * - ``{{ day.weekday }}``
     - ``Wednesday``
   * - ``{{ day.weekday.short_name }}``
     - ``Wed``
   * - ``{{ day.weekday.letter }}``
     - ``W``


``loop`` variable reference
---------------------------

Available inside every ``%% for`` block.

.. list-table::
   :header-rows: 1
   :widths: 25 50

   * - Property
     - Description
   * - ``loop.index``
     - Current iteration number, starting at 1.
   * - ``loop.index0``
     - Current iteration number, starting at 0.
   * - ``loop.first``
     - ``true`` on the very first iteration.
   * - ``loop.last``
     - ``true`` on the very last iteration.
   * - ``loop.length``
     - Total number of items in the list.
   * - ``loop.revindex``
     - Iterations remaining (including current), starting at the
       length and counting down to 1.
   * - ``loop.revindex0``
     - Like ``revindex`` but counts down to 0.


Quick cheat sheet
-----------------

::

    lang                 -> "en"  (set by --lang)

    calendar
      .year(2026)        -> Year
      .weekdays          -> (Mon, Tue, ..., Sun)  *rotated by --first-weekday*
      .firstweekday      -> 0  (0=Mon .. 6=Sun)
      .lang              -> "en"

    Year
      .value             -> 2026
      .months            -> [January, ..., December]
      .id                -> "2026"
      .isleap            -> false
      .days()            -> iterator of all Day objects

    Month
      .value             -> 1
      .name              -> "January"
      .short_name        -> "Jan"
      .days              -> [Day(1), Day(2), ..., Day(31)]
      .table             -> [[None, None, ..., Day], ...]
      .id                -> "2026-01"

    Day
      .value             -> 15
      .weekday           -> WeekDay
      .id                -> "2026-01-15"
      .is_off_day        -> true / false

    WeekDay
      .value             -> 0
      .name              -> "Monday"
      .short_name        -> "Mon"
      .letter            -> "M"
      .is_off_day        -> false


What is next
------------

Continue to :doc:`assets-and-styling` to learn how to manage stylesheets, images
and fonts in your template.

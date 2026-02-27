Variables, Expressions and Comments
====================================

Templates become powerful when you mix HTML with dynamic data. Jinja2 is the
template engine Feather Flow uses. This page covers the basics - outputting
values, creating your own variables, using filters and leaving comments.

**Key topics**

* Two syntax styles - block tags and line statements.
* Outputting values with ``{{ }}``.
* Creating variables with ``set``.
* Accessing properties with dot notation.
* Filters for transforming values.
* Comments.


Two syntax styles
-----------------

Jinja2 has a standard block syntax that uses curly braces. In addition, Feather
Flow enables a shorthand called *line statements* that starts with ``%%``. Both
are equivalent - use whichever you find more readable.

.. list-table::
   :header-rows: 1
   :widths: 25 35 35

   * - Purpose
     - Block syntax
     - Line statement
   * - Output a value
     - ``{{ year }}``
     - (same)
   * - Statement
     - ``{% set x = 1 %}``
     - ``%% set x = 1``
   * - Comment
     - ``{# a comment #}``
     - ``## a comment``

The rest of this guide uses line statements (``%%``) because they look cleaner
in HTML templates. Remember you can always switch to the block form if you
prefer.


Outputting values
-----------------

Double curly braces print a value into the HTML:

**Template:**

.. code-block:: html+jinja

   <p>Hello, {{ "world" }}!</p>

**Output:**

.. code-block:: html

   <p>Hello, world!</p>

You can output any expression - a string, a number or a variable. Jinja2
converts it to text automatically.


Setting variables
-----------------

Use ``set`` to create a variable that you can reuse later.

**Template:**

.. code-block:: html+jinja

   %% set year = calendar.year(2026)
   <h1>Planner {{ year }}</h1>

**Output:**

.. code-block:: html

   <h1>Planner 2026</h1>

The ``calendar`` object is provided by pyplaner (see :doc:`data-reference` for
the full list). Calling ``calendar.year(2026)`` creates a ``Year`` object that
knows everything about that year - its months, days, whether it is a leap year
and more.

.. tip::

   Always call ``calendar.year()`` once at the top of your template and store
   the result in a variable. Do not call it multiple times - it does the same
   work each time.

**Do:**

.. code-block:: html+jinja

   %% set year = calendar.year(2026)
   <h1>{{ year }}</h1>
   <p>{{ year }} has {{ year.months|length }} months</p>

**Don't:**

.. code-block:: html+jinja

   <h1>{{ calendar.year(2026) }}</h1>
   <p>{{ calendar.year(2026) }} again</p>


Dot notation
------------

Objects have properties you access with a dot:

**Template:**

.. code-block:: html+jinja

   %% set year = calendar.year(2026)
   %% set january = year.months[0]
   <p>First month: {{ january.name }}</p>
   <p>Month ID: {{ january.id }}</p>
   <p>Days in January: {{ january.days|length }}</p>

**Output:**

.. code-block:: html

   <p>First month: January</p>
   <p>Month ID: 2026-01</p>
   <p>Days in January: 31</p>

Use square brackets to access items by position. Positions start at zero, so
``year.months[0]`` is January and ``year.months[11]`` is December.


String slicing
--------------

You can slice strings the same way you slice lists. This is handy for
abbreviations.

**Template:**

.. code-block:: html+jinja

   %% set year = calendar.year(2026)
   %% set january = year.months[0]
   <th>{{ january.name[:3] }}</th>

**Output:**

.. code-block:: html

   <th>Jan</th>

``[:3]`` means "the first three characters". This is handy for showing short
month and weekday names in calendar tables.


String representation
---------------------

Many objects print a human-friendly value when you put them directly inside
``{{ }}``:

.. list-table::
   :header-rows: 1
   :widths: 35 30

   * - Expression
     - Output
   * - ``{{ year }}``
     - ``2026``
   * - ``{{ month }}``
     - ``January``
   * - ``{{ day }}``
     - ``15`` (the day number)
   * - ``{{ day.weekday }}``
     - ``Wednesday``

So ``{{ day }}`` is a shortcut for ``{{ day.value }}``. Both produce the same
text, but the shorter form is preferred.

**Do:**

.. code-block:: html+jinja

   <td>{{ day }}</td>

**Don't** (unnecessary - same result, more typing):

.. code-block:: html+jinja

   <td>{{ day.value }}</td>


Filters
-------

Filters transform a value. You apply them with the pipe character ``|``.

.. list-table::
   :header-rows: 1
   :widths: 40 30

   * - Expression
     - Output
   * - ``{{ "hello"|upper }}``
     - ``HELLO``
   * - ``{{ "HELLO"|lower }}``
     - ``hello``
   * - ``{{ year.months|length }}``
     - ``12``
   * - ``{{ 3.14159|round(2) }}``
     - ``3.14``

**Template:**

.. code-block:: html+jinja

   %% set year = calendar.year(2026)
   <p>{{ year.months|length }} months</p>

**Output:**

.. code-block:: html

   <p>12 months</p>

You will rarely need filters beyond ``length`` in planner templates, but they
are there if you want them.


Comments
--------

Comments are ignored by the engine and do not appear in the output.

**Line comment** (recommended in Feather Flow templates):

.. code-block:: html+jinja

   ## This line will not appear in the output.
   <p>This line will.</p>

**Block comment:**

.. code-block:: html+jinja

   {# This will not appear in the output either. #}
   <p>This line will.</p>

**HTML comment** (still appears in the output):

.. code-block:: html

   <!-- This IS visible in the generated HTML. -->

Use ``##`` or ``{# #}`` for notes to yourself. Use ``<!-- -->`` only if you want
the comment to survive into the final HTML.


Update the Mini Planner
-----------------------

Open ``pages/mini-planner.html`` and add variables for the year and the month.
Our Mini Planner covers a single month, so we pick January (``year.months[0]``).
The cover shows both the month name and the year dynamically:

.. code-block:: html+jinja

   %% set year = calendar.year(2026)
   %% set month = year.months[0]
   <!doctype html>
   <html>
   <head>
     {{ planner_head }}
     <meta charset="utf-8">
     <style>
       @page { size: 139.7mm 215.9mm; margin: 0; }
       .page {
         position: relative;
         width: 139.7mm; height: 215.9mm;
         overflow: hidden;
         page-break-after: always;
         break-after: page;
       }
       .back {
         position: absolute; inset: 0;
         width: 100%; height: 100%;
         object-fit: cover; z-index: -1;
       }
     </style>
   </head>
   <body>
     <div class="page">
       <img class="back" src="assets/mini-cover.png">
       <h1 style="text-align: center; padding-top: 70mm;">
         Mini Planner - {{ month }} {{ year }}
       </h1>
     </div>
   </body>
   </html>

Regenerate and check::

    pyplaner --html pages/mini-planner.html

The title should now read "Mini Planner - January 2026".

.. image:: ../images/mini-planner-year-title.png
   :width: 60%
   :align: center


What is next
------------

Continue to :doc:`jinja2-loops-conditionals` to learn how to repeat HTML with
loops and show content conditionally.

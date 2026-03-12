Template Parameters
===================

So far every value in the template has come from the ``calendar`` object or been
hard-coded in HTML. Template parameters let you pull values like colors, titles
and toggle flags out of the template and into a small XML file. Users can then
customize the planner from the command line without editing the template source.

**Key topics**

* Declaring parameters in ``params.xml``.
* Supported types and default values.
* Namespaces for grouping related parameters.
* Using parameters in the template.
* Overriding parameters from the command line with ``-D``.
* Live preview with parameters.


Why use parameters?
-------------------

Consider the off-day color in the Demo Planner. Without parameters you would
hard-code it:

.. code-block:: html+jinja

   %% macro day_style(day)
     {% if day.is_off_day %}color: #C00000{% endif %}
   %% endmacro

If a user wants red instead of dark red they have to open the template, find the
color and change it. With parameters you declare the color in ``params.xml``,
use ``{{ params.day_off_color }}`` in the template, and the user overrides it
on the command line.


The ``params.xml`` file
-----------------------

Create a file called ``params.xml`` in the same directory as the template:

.. code-block:: text

   planners/
     demo/
       demo.html
       params.xml           <-- new
       assets/
         ...

The file uses XML. If you are comfortable with HTML you already know the syntax.
Here is a minimal example:

.. code-block:: xml

   <?xml version="1.0" encoding="UTF-8"?>
   <params>
     <accent help="Primary accent color">#4A90D9</accent>
   </params>

The root element is always ``<params>``. Each child element declares one
parameter. The element name becomes the parameter name. The element's text
content is the default value. The optional ``help`` attribute is a
human-readable description.

For values that contain XML special characters (``<``, ``>``, ``&``) wrap the
text in ``<![CDATA[...]]>``:

.. code-block:: xml

   <pattern help="SVG pattern"><![CDATA[<circle cx="5" r="2"/>]]></pattern>


Supported types
---------------

Every parameter has a type. When omitted the type defaults to ``str``.

.. list-table::
   :header-rows: 1
   :widths: 15 15 30 30

   * - ``type=``
     - Python type
     - Parses from string via
     - Example
   * - ``str``
     - string
     - used as-is
     - ``#4A90D9``
   * - ``int``
     - integer
     - ``int(value)``
     - ``2026``
   * - ``float``
     - float
     - ``float(value)``
     - ``1.5``
   * - ``bool``
     - boolean
     - see below
     - ``true``, ``yes``, ``on``, ``1``

``str`` is the default. This means you can write:

.. code-block:: xml

   <accent help="Primary accent color">#4A90D9</accent>

instead of the longer:

.. code-block:: xml

   <accent type="str" help="Primary accent color">#4A90D9</accent>

Both are equivalent.


Bool values
~~~~~~~~~~~

Bool parameters accept the following values (case-insensitive):

.. list-table::
   :header-rows: 1
   :widths: 50 50

   * - Truthy
     - Falsy
   * - ``true``, ``yes``, ``y``, ``on``, ``1``
     - ``false``, ``no``, ``n``, ``off``, ``0``


Default values
~~~~~~~~~~~~~~

If the text content is empty or absent, the parameter defaults to ``None``.
This is useful for optional values that the user may or may not provide:

.. code-block:: xml

   <subtitle type="str" help="Optional cover subtitle"/>

In the template use a conditional to check:

.. code-block:: html+jinja

   %% if params.subtitle
   <h2>{{ params.subtitle }}</h2>
   %% endif


Namespaces
----------

Group related parameters by nesting elements. A parent element with child
elements and no ``type`` attribute becomes a namespace. The optional ``help``
attribute documents the namespace:

.. code-block:: xml

   <?xml version="1.0" encoding="UTF-8"?>
   <params>
     <year type="int" help="Planner year">2026</year>

     <colors help="Color settings">
       <accent help="Accent color">#4A90D9</accent>
       <off_day help="Off-day text color">#C00000</off_day>
       <background help="Page background">#FFFFFF</background>
     </colors>

     <cover>
       <title help="Cover title">My Planner</title>
       <subtitle type="str" help="Optional subtitle"/>
     </cover>
   </params>

In the template access nested parameters with dot notation:

.. code-block:: html+jinja

   <h1>{{ params.cover.title }}</h1>
   <div style="color: {{ params.colors.accent }};">...</div>

Namespaces can be nested as deep as you need.


Naming rules
~~~~~~~~~~~~

Parameter names must be valid Python identifiers: letters, digits and
underscores. Hyphens are **not** allowed because Jinja2 would interpret
``params.off-day`` as subtraction (``params.off`` minus ``day``). Use
underscores: ``<off_day>``, not ``<off-day>``.


Element rules summary
~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 30 30

   * - Has ``type`` or ``help``
     - Has child elements
     - Result
   * - Yes
     - No
     - Leaf parameter
   * - No
     - Yes
     - Namespace (``help`` allowed)
   * - ``type``
     - Yes
     - Error (ambiguous)
   * - No
     - No
     - Error (empty)


Using parameters in templates
-----------------------------

pyplanner injects a ``params`` variable into every template. When a
``params.xml`` file exists next to the template, ``params`` is a namespace built
from the declared defaults. When no file exists ``params`` is an empty namespace
and existing templates keep working unchanged.

Access parameters with ``{{ params.name }}``:

.. code-block:: html+jinja

   %% set year = calendar.year(params.year)

   %% macro day_style(day)
     {% if day.is_off_day %}color: {{ params.day_off_color }}{% endif %}
   %% endmacro

   <h1 style="color: {{ params.accent }};">
     {{ params.title }}
   </h1>


Full example
~~~~~~~~~~~~

``params.xml``:

.. code-block:: xml

   <?xml version="1.0" encoding="UTF-8"?>
   <params>
     <year type="int" help="Planner year">2026</year>
     <day_off_color help="Color for off-day and weekend text">
       #C00000
     </day_off_color>
   </params>

Template:

.. code-block:: html+jinja

   %% set year = calendar.year(params.year)

   %% macro day_style(day)
     {% if day.is_off_day %}color: {{ params.day_off_color }}{% endif %}
   %% endmacro

   ...

   %% for day in calendar.weekdays
   <th style="{{ day_style(day) }}">{{ day.letter }}</th>
   %% endfor


Overriding parameters from the command line
--------------------------------------------

Use ``-D`` (or ``--define``) to override one or more parameters when running
pyplanner:

.. code-block:: bash

   pyplanner planners/demo -D day_off_color=#E74C3C

Multiple parameters in one flag:

.. code-block:: bash

   pyplanner planners/demo -D year=2027 day_off_color=#FF0000

Repeated ``-D`` flags work too:

.. code-block:: bash

   pyplanner planners/demo -D year=2027 -D day_off_color=#FF0000

Use dot notation for nested parameters:

.. code-block:: bash

   pyplanner planners/demo -D colors.accent=#000000

pyplanner validates every ``-D`` override:

* Unknown keys are rejected (catches typos like ``-D acent=#FFF``).
* Values that do not match the declared type are rejected (for example
  ``-D year=abc`` when ``year`` is declared as ``int``).


Live preview with parameters
-----------------------------

Parameters work with ``--watch``. pyplanner reloads ``params.xml`` on every
file change, so you can edit the XML, save, and see the result in the browser
immediately:

.. code-block:: bash

   pyplanner planners/demo --watch -D day_off_color=#FF0000

Any ``-D`` overrides you pass on the command line are re-applied after each
reload.


Update the Demo Planner
-----------------------

Create ``planners/demo/params.xml`` with three parameters - the planner year,
the month and the off-day color that was previously hard-coded in the
``day_color`` macro:

.. code-block:: xml

   <?xml version="1.0" encoding="UTF-8"?>
   <params>
     <year type="int" help="Planner year">2026</year>
     <month type="int" help="Month (1=January, 12=December)">1</month>
     <day_off_color help="Color for off-day and weekend text">
       #C00000
     </day_off_color>
   </params>

Open ``planners/demo/demo.html`` and replace the hard-coded year, month and
color with parameter references. After this page your template should look like
this:

.. code-block:: html+jinja

   %% set year = calendar.year(params.year)
   %% set month = year.months[params.month - 1]

   %% macro day_color(day)
     {% if day.is_off_day %}{{ params.day_off_color }}{% else %}#000000{% endif %}
   %% endmacro

   %% macro month_table(month)
     %% for week in month.table
     <tr>
       %% for day in week
       %% if day is not none
       <td style="color: {{ day_color(day) }}">{{ day }}</td>
       %% else
       <td></td>
       %% endif
       %% endfor
     </tr>
     %% endfor
   %% endmacro

   <!doctype html>
   <html>
   <head>
     <meta charset="utf-8">
     <style>
       @page { size: 139.7mm 215.9mm; margin: 0; }
       html, body { margin: 0; padding: 0; height: 100%; }
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

     ## -- Cover page --
     <div class="page">
       <img class="back" src="{{ base }}/assets/cover.png">
       <h1 style="text-align: center; padding-top: 70mm;">
         Demo Planner - {{ month }} {{ year }}
       </h1>
     </div>

     ## -- Month calendar --
     <div class="page" id="{{ month.id }}">
       <img class="back" src="{{ base }}/assets/calendar.png">
       <h2 style="text-align: center; margin-top: 15mm;
                  font-size: 22pt; letter-spacing: 5mm;">
         {{ month }}
       </h2>
       <p style="text-align: center; font-size: 14pt;">
         {{ year }}
       </p>
       <table style="width: calc(100% - 10mm);
                     margin: 10mm 5mm 0 5mm;
                     border-collapse: collapse;
                     font-size: 14pt; text-align: center;
                     table-layout: fixed;">
         <thead>
           <tr>
             %% for wd in calendar.weekdays
             <th style="color: {{ day_color(wd) }}">{{ wd.short_name }}</th>
             %% endfor
           </tr>
         </thead>
         <tbody>
           {{ month_table(month) }}
         </tbody>
       </table>
     </div>

   </body>
   </html>

Three lines changed compared to the previous version:

1. ``calendar.year(2026)`` became ``calendar.year(params.year)`` - the year is
   now configurable.
2. ``year.months[0]`` became ``year.months[params.month - 1]`` - the month is
   now configurable. We subtract 1 because the list is zero-indexed but the
   parameter uses human-friendly numbering (1 = January).
3. ``#C00000`` in ``day_color`` became ``{{ params.day_off_color }}`` - the
   color is now configurable.

Regenerate with the defaults::

    pyplanner planners/demo

The output looks exactly the same as before. Now try overriding all three
parameters::

    pyplanner planners/demo -D year=2027 month=6 day_off_color=#0000CC

The cover now reads "Demo Planner - June 2027" and weekends appear in blue
instead of dark red. The template itself did not change - only the command-line
arguments did.


What is next
------------

Continue to :doc:`assets-and-styling` to learn how to manage stylesheets,
images and fonts in your template.

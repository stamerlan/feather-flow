Macros
======

When the same block of HTML appears in several places you can extract it into a
*macro* - a reusable template fragment that you call like a function. This page
shows how to define, call and organize them.

**Key topics**

* Defining a macro with ``macro`` / ``endmacro``.
* Calling a macro and passing arguments.
* Content macros vs attribute macros.
* Practical examples for calendar tables and day styling.
* Where to place macros in your template.


Defining a macro
----------------

A macro starts with ``%% macro name(parameters)`` and ends with ``%% endmacro``.
Everything between them is the macro body.

**Template:**

.. code-block:: html+jinja

   %% macro greeting(name)
   <p>Hello, {{ name }}!</p>
   %% endmacro

   {{ greeting("Alice") }}
   {{ greeting("Bob") }}

**Output:**

.. code-block:: html

   <p>Hello, Alice!</p>
   <p>Hello, Bob!</p>

The macro is called with ``{{ greeting("Alice") }}``. The argument ``"Alice"``
is assigned to the parameter ``name`` inside the body.


Multiple parameters
~~~~~~~~~~~~~~~~~~~

Macros can accept more than one parameter:

**Template:**

.. code-block:: html+jinja

   %% macro badge(label, color)
   <span style="color: {{ color }};">{{ label }}</span>
   %% endmacro

   {{ badge("Weekend", "red") }}
   {{ badge("Workday", "black") }}

**Output:**

.. code-block:: html

   <span style="color: red;">Weekend</span>
   <span style="color: black;">Workday</span>


Content macros vs attribute macros
----------------------------------

A *content macro* returns a chunk of HTML that you insert into the page:

.. code-block:: html+jinja

   %% macro month_table(month)
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
   %% endmacro

You call it where you want the rows to appear:

.. code-block:: html+jinja

   <table>
     <tbody>
       {{ month_table(january) }}
     </tbody>
   </table>

An *attribute macro* returns a small fragment meant to be placed inside an HTML
tag - for example a ``style`` attribute:

.. code-block:: html+jinja

   %% macro day_style(day)
   {% if day.is_off_day %} style="color: #C00000"{% endif %}
   %% endmacro

You call it inside the opening tag with a special ``{{-`` syntax that strips the
whitespace before the output:

.. code-block:: html+jinja

   <th {{- day_style(day) }}>{{ day.name[:3] }}</th>

**Output for a weekday:**

.. code-block:: html

   <th>Mon</th>

**Output for Saturday:**

.. code-block:: html

   <th style="color: #C00000">Sat</th>

The ``-`` after ``{{`` removes the space that would otherwise appear before
``style``. Without it you would get ``<th  style="...">``.

.. tip::

   Use ``{{-`` (with the dash) when inserting a macro result directly into an
   HTML tag to avoid extra spaces.


Combining macros
----------------

Macros can call other macros. For example, a ``month_table`` macro can use
``day_style`` to color off-days:

.. code-block:: html+jinja

   %% macro day_style(day)
     {% if day.is_off_day %} style="color: #C00000"{% endif %}
   %% endmacro

   %% macro month_table(month)
     %% for week in month.table
       <tr>
         %% for day in week
           %% if day is not none
             <td {{- day_style(day) }}>
               <a href="#{{ day.id }}">{{ day }}</a>
             </td>
           %% else
             <td></td>
           %% endif
         %% endfor
       </tr>
     %% endfor
   %% endmacro

If you later want to change how off-days look you only edit ``day_style`` once
and every table that calls it picks up the change.


Where to place macros
---------------------

Define all macros before the ``<!doctype html>`` line:

**Do:**

.. code-block:: html+jinja

   %% macro day_style(day)
     {% if day.is_off_day %} style="color: #C00000"{% endif %}
   %% endmacro

   %% macro month_table(month)
     ...
   %% endmacro

   <!doctype html>
   <html>
   ...

**Don't** - define macros in the middle of the HTML:

.. code-block:: html+jinja

   <!doctype html>
   <html>
   <body>
     %% macro day_style(day)
       ...
     %% endmacro
     ...

Keeping macros at the top makes them easy to find and ensures they are defined
before they are called.


Do and don't summary
--------------------

.. list-table::
   :header-rows: 1
   :widths: 50 50

   * - Do
     - Don't
   * - Place macros before ``<!doctype html>``.
     - Scatter macros throughout the body.
   * - Use macros to avoid copy-pasting repeated HTML.
     - Duplicate the same table code in five places.
   * - Use ``{{-`` when inserting into an HTML tag.
     - Use ``{{`` inside a tag (leaves extra whitespace).
   * - Close every macro with ``%% endmacro``.
     - Forget ``endmacro`` - the template will not render.


Update the Mini Planner
-----------------------

Refactor the month calendar from the previous page. Move the off-day styling and
the table rows into macros. Your ``pages/mini-planner.html`` should now look
like this:

.. code-block:: html+jinja

   %% set year = calendar.year(2026)
   %% set month = year.months[0]

   %% macro day_color(day)
     {% if day.is_off_day %}#C00000{% else %}#000000{% endif %}
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

     ## -- Cover page --
     <div class="page">
       <img class="back" src="assets/mini-cover.png">
       <h1 style="text-align: center; padding-top: 70mm;">
         Mini Planner - {{ month }} {{ year }}
       </h1>
     </div>

     ## -- Month calendar --
     <div class="page" id="{{ month.id }}">
       <img class="back" src="assets/mini-calendar.png">
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
             <th style="color: {{ day_color(wd) }}">{{ wd.name[:3] }}</th>
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

Regenerate::

    pyplaner --html pages/mini-planner.html

The output should look the same as before, but the template is now
shorter and easier to maintain. The ``day_color`` macro can be
reused on day pages later.


What is next
------------

Continue to :doc:`data-reference` for a complete list of every
object and property available in your templates.

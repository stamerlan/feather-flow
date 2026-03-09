Live Preview
============

Generating a PDF every time you change a color or move an element is slow. This
page shows a faster workflow: start pyplanner in watch mode and let it
regenerate the HTML and reload the browser automatically each time you save a
file.

**Key topics**

* Starting the live-reload server with ``--watch``.
* The edit - save - reload loop.
* Troubleshooting common issues.


Start the live-reload server
----------------------------

From the repository root run::

    pyplanner planners/mini-planner --watch

pyplanner generates ``mini-planner.html``, starts a local server and prints the
address::

    Serving on http://127.0.0.1:5500
    Ctrl+C to exit

Open that URL in any browser. The page shows the fully rendered planner with
all background images, fonts and stylesheets loaded correctly.


The edit - save - reload loop
-----------------------------

With the server running your workflow looks like this:

1. **Edit** the template ``planners/mini-planner/mini-planner.html`` or any
   asset (CSS, images) in any editor you like.

2. **Save** the file.

3. **View** - pyplanner detects the change, regenerates the HTML and the browser
   reloads automatically.

That is it. No manual re-run, no extra extensions, no specific editor required.
Use the editor and browser you are most comfortable with.

.. tip::

   Pass ``--verbose`` to see "Browser connected" and "Regenerating..." messages
   in the terminal so you know exactly when a rebuild happens.


Why not edit the generated file directly?
-----------------------------------------

The generated HTML is a *build artifact*. It is overwritten every time
pyplanner regenerates. Any changes you make to it will be lost. Always edit the
source template.

.. warning::

   Never edit the generated HTML file. Edit the template and save.


Troubleshooting
---------------

Images or fonts are missing in the browser
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Make sure you started pyplanner from the repository root. The generated HTML
references assets via ``{{ base }}/`` which expands to the template directory
path. The live-reload server serves files from the planner directory, so all
assets must be reachable relative to the template.

Browser does not reload
~~~~~~~~~~~~~~~~~~~~~~~

Check that pyplanner is still running in the terminal. If it stopped (for
example after an error), restart it with the same ``--watch`` command.

Browser shows Jinja2 syntax
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You are opening the template file directly. Navigate to the URL printed by
pyplanner (``http://127.0.0.1:5500``) instead.


Do and don't summary
--------------------

.. list-table::
   :header-rows: 1
   :widths: 50 50

   * - Do
     - Don't
   * - Run pyplanner from the repository root.
     - ``cd`` into the planner directory (output overwrites the template).
   * - Open the URL printed by pyplanner.
     - Open the template file (it contains Jinja2 syntax the browser cannot
       understand).
   * - Edit the template, then save.
     - Edit the generated HTML (it is overwritten on every build).
   * - Use ``--watch`` for fast iteration.
     - Generate PDF every time (much slower).


Summary
-------

You have completed the Designer Guide. Here is a recap of what you learned:

1. **Project structure** - each planner in its own directory under
   ``planners/``, assets alongside the template.
2. **Template basics** - the ``.page`` div, asset paths, background images.
3. **Jinja2 variables** - ``{{ }}``, ``%% set``, dot notation, filters,
   comments.
4. **Loops and conditionals** - ``for``/``endfor``, ``if``/``endif``,
   ``is none``, the ``loop`` variable.
5. **Macros** - reusable blocks with ``macro``/``endmacro``.
6. **Data reference** - ``calendar``, Year, Month, Day, WeekDay and all their
   properties.
7. **Assets** - path rules, CSS patterns, custom fonts.
8. **Live preview** - ``pyplanner --watch`` for fast iteration with any editor
   and browser.

Try changing colors, fonts or layouts in the Mini Planner. When you are
comfortable, create your own template from scratch.

Happy designing!

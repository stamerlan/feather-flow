Project Structure
=================

Before you create your first template it helps to know where files live and how
they turn into a finished planner. This page walks through the folder layout and
the rendering pipeline.

**Key topics**

* Repository folder layout.
* Where to put templates and assets.
* How pyplaner turns a template into HTML or PDF.


Folder layout
-------------

After you clone the repository you will see a structure like this::

    feather-flow/
    |-- assets/
    |   |-- cover.png
    |   |-- year.png
    |   |-- day.png
    |   |-- month-jan.png
    |   |-- month-feb.png
    |   |-- ...
    |   |-- cormorant-garamond.css
    |   |-- cormorant-garamond-normal-latin.woff2
    |   +-- cormorant-garamond-italic-latin.woff2
    |
    |-- pages/
    |   +-- (your templates go here)
    |
    |-- src/pyplaner/           <-- Python source (you rarely
    |   |-- ...                     need to touch this)
    |
    +-- docs/                   <-- Sphinx documentation

The two folders you will work with most are:

``pages/``
    Contains Jinja2/HTML template files. Each template describes the full
    planner - cover, calendars, day pages and so on. You can have several
    templates side by side.

``assets/``
    Contains everything the templates reference - stylesheets, background images
    and font files.


Where to put new files
----------------------

Follow these simple rules:

.. list-table::
   :header-rows: 1
   :widths: 30 40 30

   * - File type
     - Location
     - Example
   * - Template
     - ``pages/``
     - ``pages/mini-planner.html``
   * - Stylesheet
     - ``assets/``
     - ``assets/mini-planner.css``
   * - Background image
     - ``assets/``
     - ``assets/mini-cover.png``
   * - Font file
     - ``assets/``
     - ``assets/myfont.woff2``

.. tip::

   Keep file names lowercase and use hyphens instead of spaces.
   Good: ``my-planner.html``. Bad: ``My Planner.html``.


The rendering pipeline
----------------------

When you run pyplaner it follows these steps:

1. **Load the template** from ``pages/``.
2. **Inject calendar data** - a ``calendar`` object and a helper string called
   ``planner_head`` become available inside the template.
3. **Render with Jinja2** - loops, variables and macros in the template are
   evaluated and plain HTML is produced.
4. **Write the output** to the current working directory.

   * ``--html`` flag - writes an ``.html`` file you can open in any browser.
   * ``--pdf`` flag (the default) - opens the HTML in a headless Chromium
     browser and prints it to PDF.

::

    +------------------+     +----------+     +-------------+
    | pages/my.html    |---->| pyplaner |---->| my.html     |
    | assets/my.css    |     |          |     | my.pdf      |
    | assets/back.png  |     +----------+     +-------------+
    +------------------+      (Jinja2 +        (in current
                               Playwright)      directory)

.. warning::

   The output files are written to the directory where you run the command, not
   next to the template. If you run ``pyplaner pages/my-planner.html`` from the
   repository root the output lands in the repository root as
   ``my-planner.html`` or ``my-planner.pdf``.


What is next
------------

Now that you know where everything lives, continue to :doc:`template-basics` to
create your first template page.

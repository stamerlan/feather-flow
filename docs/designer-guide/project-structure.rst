Project Structure
=================

Before you create your first template it helps to know where files live and how
they turn into a finished planner. This page walks through the folder layout and
the rendering pipeline.

**Key topics**

* Repository folder layout.
* Where to put templates and assets.
* How pyplanner turns a template into HTML or PDF.


Folder layout
-------------

After you clone the repository you will see a structure like this::

    feather-flow/
    |-- planners/
    |   +-- ff-2026/
    |       |-- ff-2026.html
    |       +-- assets/
    |           |-- ff-2026.css
    |           |-- cover.png
    |           |-- year.png
    |           |-- day.png
    |           |-- jan.png
    |           |-- ...
    |           |-- cormorant-garamond.css
    |           |-- cormorant-garamond-normal-latin.woff2
    |           +-- cormorant-garamond-italic-latin.woff2
    |
    |-- src/pyplanner/           <-- Python source (you rarely
    |   |-- ...                      need to touch this)
    |
    +-- docs/                   <-- Sphinx documentation

Each planner lives in its own self-contained directory under ``planners/``.
The directory holds the Jinja2/HTML template and an ``assets/`` subfolder
with all stylesheets, images and fonts the template needs.

``planners/<name>/<name>.html``
    The Jinja2/HTML template file that describes the full planner - cover,
    calendars, day pages and so on.

``planners/<name>/assets/``
    Everything the template references - stylesheets, background images and font
    files.

.. tip::

   Keep file names lowercase and use hyphens instead of spaces.
   Good: ``my-planner.html``. Bad: ``My Planner.html``.


The rendering pipeline
----------------------

When you run pyplanner it follows these steps:

1. **Load the template** from the planner directory.
2. **Inject template variables** - ``base``, ``calendar`` and ``lang`` become
   available inside the template.
3. **Render with Jinja2** - loops, variables and macros in the template are
   evaluated and plain HTML is produced.
4. **Write the output** to the current working directory.

   * ``--html`` flag - writes an ``.html`` file you can open in any browser.
   * ``--pdf`` flag (the default) - opens the HTML in a headless Chromium
     browser and prints it to PDF. Asset paths are resolved relative to the
     template's directory so the PDF is correct regardless of where you run the
     command.

::

    planners/my-planner/
    |-- my-planner.html  --+
    +-- assets/            |   +----------+   +---------------+
        |-- my.css         +-->| pyplanner |-->| my-planner.pdf|
        +-- back.png           +----------+   +---------------+
                               (Jinja2 +       (in current
                                Playwright)     directory)

.. warning::

   The output files are written to the directory where you run the command. If
   you run ``pyplanner --html my-planner.html`` from the planner directory, the
   output lands in the planner directory and overwrites the template file.


What is next
------------

Now that you know where everything lives, continue to :doc:`template-basics` to
create your first template page.

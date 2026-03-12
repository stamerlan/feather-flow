Rendering Planners
==================

The :class:`~pyplanner.Planner` class ties a Jinja2/HTML template together with
a :class:`~pyplanner.Calendar` and template parameters, then renders the result
to HTML or PDF.

Creating a Planner
------------------

.. code-block:: python

    from pyplanner import Calendar, Planner

    cal = Calendar()
    planner = Planner("planners/demo/demo.html", calendar=cal)

The template path must point to a Jinja2/HTML file. The Jinja2 environment is
configured with:

- ``%%`` as the line statement prefix
- ``##`` as the line comment prefix
- ``trim_blocks`` and ``lstrip_blocks`` enabled
- Autoescaping for HTML

The template directory (parent of the template file) is used as the Jinja2
file-system loader root.

Template parameters
-------------------

Templates may accept parameters defined in a ``params.xml`` file next to the
template. :class:`~pyplanner.Params` loads the schema and produces a
:class:`~types.SimpleNamespace` tree:

.. code-block:: python

    from pyplanner import Params

    params = Params.load_xml("planners/demo/params.xml")
    ns = params.apply()

    print(ns.year)           # 2026
    print(ns.month)          # 1
    print(ns.day_off_color)  # #C00000

Override individual values with ``-D``-style strings:

.. code-block:: python

    ns = params.apply(["year=2027", "day_off_color=#0000FF"])
    print(ns.year)           # 2027

Nested parameters use dot notation:

.. code-block:: python

    # Given a params.xml with <colors><primary>#FFF</primary></colors>
    ns = params.apply(["colors.primary=#000"])
    print(ns.colors.primary)  # #000

The ``params.xml`` format
^^^^^^^^^^^^^^^^^^^^^^^^^

The XML schema uses ``<params>`` as the root element. Leaf parameters have a
``type`` attribute (``str``, ``int``, ``float`` or ``bool``) and their text
content is the default value. Namespace elements group related parameters under
a nested namespace:

.. code-block:: xml

    <?xml version="1.0" encoding="UTF-8"?>
    <params>
      <year type="int" help="Planner year">2026</year>
      <accent help="Primary accent color">#4A90D9</accent>
      <show_notes type="bool" help="Include notes">yes</show_notes>
      <colors help="Brand colors">
        <primary help="Primary brand color">#4A90D9</primary>
        <weekend help="Weekend highlight">#FDD</weekend>
      </colors>
    </params>

Rules:

- Element names must be valid Python identifiers (use underscores, not hyphens).
- Omitting ``type`` defaults to ``str``.
- Boolean values accept ``true``/``false``, ``yes``/``no``, ``y``/``n``,
  ``on``/``off``, ``1``/``0`` (case-insensitive).
- Use ``<![CDATA[...]]>`` for values containing XML special characters
  (e.g. inline SVG).

Programmatic schema
^^^^^^^^^^^^^^^^^^^

You can also build a :class:`~pyplanner.Params` from a dict without an XML file:

.. code-block:: python

    from pyplanner import Params

    params = Params({
        "year": {"type": "int", "default": 2026},
        "accent": {"type": "str", "default": "#4A90D9"},
    })
    ns = params.apply(["year=2027"])

Rendering to HTML
-----------------

:meth:`Planner.html() <pyplanner.Planner.html>` renders the template and returns
an HTML string:

.. code-block:: python

    html = planner.html(base="planners/demo")
    with open("demo.html", "w", encoding="utf-8") as f:
        f.write(html)

The ``base`` parameter controls how asset paths (images, CSS, fonts) are
resolved. Templates reference assets as ``{{ base }}/assets/...``. When ``base``
is a relative path, assets resolve relative to wherever the output HTML is
saved. When ``base`` is ``None``, it defaults to the template directory's
``file://`` URI.

``base`` is a render-time parameter rather than a constructor argument because
the correct value depends on *where the output is written*, not on the template
location. When generating HTML to a file, ``base`` should be a relative path
from the output to the template directory. When generating a PDF, it should be a
``file://`` URI. The ``--watch`` mode needs yet another value (relative to the
livereload server root). Making it a render-time parameter lets the same
``Planner`` instance produce output for different contexts without
reconstruction.

Rendering to PDF
----------------

:meth:`Planner.pdf() <pyplanner.Planner.pdf>` launches a headless Chromium
browser via Playwright, loads the rendered HTML and prints it to PDF:

.. code-block:: python

    pdf_bytes = planner.pdf()
    with open("demo.pdf", "wb") as f:
        f.write(pdf_bytes)

The PDF renderer:

- Routes ``file://`` requests to the local file system so images and fonts load
  correctly.
- Waits for web fonts to finish loading before printing.
- Respects CSS ``@page`` rules for page size and margins.
- Extracts ``.page`` element IDs and adds year/month bookmarks to the PDF
  outline automatically.

Page size and margins are controlled entirely by CSS ``@page`` rules in the
template's stylesheet, not by API parameters. An earlier version accepted
``margin_top``, ``margin_bottom``, etc. as parameters to ``pdf()``. This created
two competing sources of truth: the CSS and the Python API. Removing the API
parameters makes CSS the single source for page geometry, which is what
designers expect. Playwright's ``prefer_css_page_size=True`` flag ensures the
browser respects the template's ``@page`` declarations.

Template context variables
--------------------------

Every template receives four variables:

``base``
    Base URL string for resolving asset paths.

``calendar``
    The :class:`~pyplanner.Calendar` instance. Call ``calendar.year(n)`` to
    build a year. Access ``calendar.weekdays`` for the ordered weekday list.

``lang``
    Language code string (e.g. ``"en"``).

``params``
    The :class:`~types.SimpleNamespace` tree from ``params.xml``.

Live preview
------------

For interactive design work, the :func:`~pyplanner.watch` function starts a
livereload server that rebuilds the HTML on every file change:

.. code-block:: python

    from pyplanner import Planner, watch

    planner = Planner("planners/demo/demo.html")
    watch(planner, "demo.html")

This is equivalent to running ``pyplanner planners/demo --watch`` on the command
line.

.. warning::

    The ``livereload`` package is imported lazily inside ``watch()`` rather than
    at module level. Importing it triggers ``logging.basicConfig()`` which
    alters the global logging state of the host application. By deferring the
    import to call time, the side effect is confined to the moment the user
    explicitly opts into live preview, leaving the logging setup untouched for
    all other code paths. If you use pyplanner as a library, be aware that
    calling :func:`~pyplanner.watch` will trigger that side effect and may
    affect your log handlers.

API reference
-------------

.. autoclass:: pyplanner.Planner
   :members: html, pdf

.. autoclass:: pyplanner.Params
   :members: load_xml, apply

.. autofunction:: pyplanner.params.parse_bool

Developer Guide
===============

This guide shows how to use **pyplanner** as a Python library in your own
project. It walks through the calendar model, holiday providers, template
rendering and PDF post-processing step by step with code examples you can copy
and adapt.

If you are looking for how to *design planner templates* (HTML/CSS), see the
:doc:`/designer-guide/intro`. If you want to contribute to the pyplanner package
itself, see :doc:`/internals/intro`.

Install from a local clone::

    pip install /path/to/feather-flow

Or install in editable mode for development::

    pip install -e /path/to/feather-flow

Playwright needs a browser binary for PDF rendering. Install it once after the
package is installed::

    playwright install chromium

The shortest path from zero to a rendered planner:

.. code-block:: python

    from pyplanner import Calendar, Planner, Params

    calendar = Calendar()
    params = Params.load_xml("planners/demo/params.xml").apply()

    planner = Planner(
        "planners/demo/demo.html",
        calendar=calendar,
        params=params,
    )

    # Render to HTML string
    html = planner.html(base="planners/demo")

    # Or render to PDF bytes
    pdf_bytes = planner.pdf()
    with open("demo.pdf", "wb") as f:
        f.write(pdf_bytes)

The sections that follow explain each building block in detail.

.. toctree::
   :maxdepth: 1

   calendar-and-days
   holidays
   rendering
   pdf-postprocessing
   progress-tracking

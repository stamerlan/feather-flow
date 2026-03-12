PDF Post-processing
===================

Chromium's print-to-PDF produces valid but bloated files. Every page is rendered
independently so identical assets (background images, SVG patterns, transparency
masks) are embedded as separate PDF objects on every page. A 365-day planner can
easily be 10x larger than necessary.

Pyplanner provides two post-processing utilities that shrink the output and add
navigation.

Optimization lives in its own module (``pdfopt``) with a simple
bytes-in/bytes-out API. It is *not* called inside ``Planner.pdf()``. This
separation keeps the rendering path focused on Jinja2 and Playwright, and lets
callers choose whether to optimize. The CLI exposes ``--opt/--no-opt``; library
users call ``optimize()`` explicitly.

Optimizing PDF size
-------------------

:func:`~pyplanner.pdfopt.optimize` accepts raw PDF bytes, rewrites the internal
structure and returns optimized bytes:

.. code-block:: python

    from pyplanner.pdfopt import optimize

    with open("planner.pdf", "rb") as f:
        raw = f.read()

    optimized = optimize(raw)

    with open("planner-opt.pdf", "wb") as f:
        f.write(optimized)

    saved = 1 - len(optimized) / len(raw)
    print(f"Saved {saved:.0%}")

The optimization passes are:

1. **Image deduplication** - identical Image XObjects are merged into a single
   canonical copy. The full PDF object graph is walked to rewire all references.
   This handles images inside Form XObjects, tiling Patterns and transparency
   masks.

2. **ProcSet stripping** - obsolete ``/ProcSet`` arrays are removed from every
   ``/Resources`` dictionary. These have been ignored by PDF readers since
   PDF 1.4 (2001).

3. **Form XObject deduplication** - after image dedup, Form XObjects that
   previously differed only by which copy of an image they referenced now have
   identical content streams. They are merged the same way as images.

4. **Recompression** - the file is re-serialized with object stream packaging
   and Flate recompression.

Adding bookmarks
----------------

:func:`~pyplanner.pdfbookmarks.add_bookmarks` inserts outline entries (a
table-of-contents sidebar in PDF viewers):

.. code-block:: python

    from pyplanner.pdfbookmarks import add_bookmarks

    with open("planner.pdf", "rb") as f:
        pdf_bytes = f.read()

    # Top-level bookmarks: (title, 0-based page number)
    pdf_bytes = add_bookmarks(pdf_bytes, [("2026", 1),])

    # Nested bookmarks under "2026":
    pdf_bytes = add_bookmarks(pdf_bytes, [
        ("January", 2),
        ("February", 33),
    ], parent=["2026"])

    with open("planner-bookmarked.pdf", "wb") as f:
        f.write(pdf_bytes)

The ``parent`` argument is a list of bookmark titles forming a path from the
root to the desired parent node.

.. note::

    When rendering via :meth:`Planner.pdf() <pyplanner.Planner.pdf>`, bookmarks
    are added automatically from ``.page`` element IDs in the HTML. You only
    need :func:`~pyplanner.pdfbookmarks.add_bookmarks` if you are building a
    custom pipeline.

Putting it together
-------------------

A typical post-processing pipeline after ``Planner.pdf()``:

.. code-block:: python

    from pyplanner import Calendar, Planner
    from pyplanner.pdfopt import optimize

    cal = Calendar()
    planner = Planner("planners/ff-2026/ff-2026.html", calendar=cal)

    pdf_bytes = planner.pdf()     # bookmarks added automatically
    pdf_bytes = optimize(pdf_bytes)

    with open("ff-2026.pdf", "wb") as f:
        f.write(pdf_bytes)

This matches what the CLI does when you run
``pyplanner planners/ff-2026 --pdf``.

API reference
-------------

.. autofunction:: pyplanner.pdfopt.optimize

.. autofunction:: pyplanner.pdfbookmarks.add_bookmarks

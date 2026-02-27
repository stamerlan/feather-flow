Assets and Styling
==================

Every planner needs images, stylesheets and possibly custom fonts. This page
explains where to put those files, how to reference them from a template and the
CSS patterns that make pages look correct in both the browser and the generated
PDF.

**Key topics**

* Where to store CSS, images and fonts.
* How asset paths work (relative to the template directory).
* Key CSS classes: ``@page``, ``.page``, ``.back``.
* Page breaks.
* Custom fonts with ``@font-face``.
* Do and don't for asset management.


Where assets live
-----------------

All assets go in the ``assets/`` folder at the repository root. Templates live
in ``pages/``. The two folders are siblings::

    feather-flow/
    |-- assets/
    |   |-- cover.png
    |   |-- my-planner.css
    |   +-- cormorant-garamond.woff2
    |
    +-- pages/
        +-- mini-planner.html

This layout matters because paths inside your template are resolved relative to
the project root directory. Since ``assets/`` sits next to ``pages/``, the
correct relative path from any template to any asset is ``assets/<filename>``.


Path rules
----------

.. list-table::
   :header-rows: 1
   :widths: 50 50

   * - Do
     - Don't
   * - ``href="assets/my.css"``
     - ``href="/assets/my.css"`` (leading slash - breaks PDF)
   * - ``src="assets/mini-cover.png"``
     - ``src="C:/repo/assets/mini-cover.png"`` (absolute - breaks
       on other machines)
   * - ``src="assets/mini-cover.png"``
     - ``src="../assets/mini-cover.png"`` (wrong - assets is a
       sibling of pages, not a parent)

The path ``assets/my.css`` works because pyplaner resolves it relative to the
current working directory that contains this project. During PDF generation the
headless browser intercepts these paths and loads the files from disk.

.. warning::

   Never use absolute paths or paths that start with ``/``. They will break when
   someone else clones the repository or when the PDF generator runs.


Linking a stylesheet
--------------------

Use a standard ``<link>`` tag inside ``<head>``:

.. code-block:: html+jinja

   <head>
     {{ planner_head }}
     <meta charset="utf-8">
     <link rel="stylesheet" href="assets/my-planner.css">
   </head>

You can link multiple stylesheets. For example you might have one for layout and
one for fonts:

.. code-block:: html+jinja

   <link rel="stylesheet" href="assets/my-planner.css">
   <link rel="stylesheet" href="assets/cormorant-garamond.css">


Adding images
-------------

Background images use ``<img class="back">``:

.. code-block:: html+jinja

   <div class="page">
     <img class="back" src="assets/mini-cover.png">
     <h1>My Planner</h1>
   </div>

Inline images (such as icons or decorations) use a regular ``<img>`` tag without
the ``back`` class:

.. code-block:: html+jinja

   <img src="assets/icon-star.png"
        style="width: 10mm; height: 10mm;">

.. tip::

   Use PNG for images with transparency and JPG for photos. Keep images at a
   reasonable resolution - 300 DPI at A4 size is roughly 2480 x 3508 pixels.
   For non-detailed backgrounds 120 DPI is enough (~1024 x 1536 on A4 page).


Key CSS patterns
----------------

These are the essential CSS patterns every planner template needs. The Mini
Planner already uses them in its ``<style>`` block.


``@page`` - paper size
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: css

   @page {
     size: 139.7mm 215.9mm;
     margin: 0;
   }

This tells the PDF generator which paper size to use and removes printer
margins. Common values:

* ``size: letter;`` - US Letter (8.5 x 11 in).
* ``size: A4;`` - international A4 (210 x 297 mm).
* ``size: A5;`` - half of A4 (148 x 210 mm).
* ``size: 139.7mm 215.9mm;`` - half letter (5.5 x 8.5 in).
* ``size: 200mm 300mm;`` - custom width and height.

When you change the ``@page`` size you must also update the ``.page`` div
dimensions to match so the on-screen preview is accurate.


``.page`` - page container
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: css

   .page {
     position: relative;
     width: 139.7mm; height: 215.9mm;
     overflow: hidden;
     page-break-after: always;
     break-after: page;
   }

Every ``<div class="page">`` becomes one printed page. The fixed dimensions must
match the paper size set in ``@page`` (the example above uses half letter -
139.7 x 215.9 mm). ``overflow: hidden`` crops anything that extends beyond the
page edge.


``.back`` - full-bleed image
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: css

   .back {
     position: absolute; inset: 0;
     width: 100%; height: 100%;
     object-fit: cover; z-index: -1;
   }

Place an ``<img class="back">`` inside a ``.page`` div and it stretches to fill
the entire page behind all other content.


Page breaks
~~~~~~~~~~~

The rule ``page-break-after: always`` on ``.page`` is what separates pages in
the PDF. If you create your own CSS make sure every page container has this
rule. Without it all pages will merge into one long document.

.. code-block:: css

   .my-page {
     page-break-after: always;
     break-after: page;
   }


Custom fonts
------------

Place font files in ``assets/`` and create a small CSS file for them.

``assets/cormorant-garamond.css`` from the project:

.. code-block:: css

   @font-face {
     font-family: "Cormorant Garamond";
     font-style: normal;
     font-weight: 400;
     src: url(cormorant-garamond-normal-latin.woff2)
          format('woff2');
   }

   @font-face {
     font-family: "Cormorant Garamond";
     font-style: italic;
     font-weight: 400;
     src: url(cormorant-garamond-italic-latin.woff2)
          format('woff2');
   }

Because both the CSS file and the font files sit in the same ``assets/`` folder
the ``url()`` path is just the file name with no directory prefix.

Link the font CSS from your template:

.. code-block:: html+jinja

   <link rel="stylesheet"
         href="assets/cormorant-garamond.css">

Then use the font in your styles:

.. code-block:: css

   .page {
     font-family: "Cormorant Garamond", Georgia, serif;
   }

.. tip::

   If you add a new font, provide both normal and italic variants (or whichever
   variants your design uses). Browsers will synthesize missing styles, but the
   result often looks worse than a real italic or bold file.


Do and don't summary
--------------------

.. list-table::
   :header-rows: 1
   :widths: 50 50

   * - Do
     - Don't
   * - Put all assets in ``assets/``.
     - Scatter files across random directories.
   * - Use relative paths: ``assets/my.css``.
     - Use absolute paths or leading slashes.
   * - Use ``@page { size: A4; margin: 0; }`` for paper size.
     - Set paper size through other means.
   * - Define ``.page`` and ``.back`` classes once.
     - Duplicate page sizing rules in every div.
   * - Use WOFF2 for custom fonts.
     - Use TTF or OTF (larger files, slower loading).


Update the Mini Planner
-----------------------

Add day pages to the Mini Planner. Each day gets its own page with a background
image and a header. Open ``pages/mini-planner.html`` and add the following after
the month calendar div, just before ``</body>``:

.. code-block:: html+jinja

   ## -- Day pages --
   %% for day in month.days
   <div class="page" id="{{ day.id }}">

     ## Put header index behind grid
     <img class="back" src="assets/mini-page.png"
          style="z-index: -2;">

     ## Square grid graph paper
     <div class="back">
       <svg xmlns="http://www.w3.org/2000/svg"
            width="139.7mm" height="215.9mm"
            viewBox="0 0 139.7 215.9">
         <defs>
           <pattern id="grid" width="5" height="5"
                    patternUnits="userSpaceOnUse">
             <path d="M 5 0 L 0 0 0 5"
                   fill="none" stroke="#c0c0c0"
                   stroke-width="0.2"/>
           </pattern>
         </defs>
         <rect x="10" y="25" width="120.1" height="180.1"
               fill="url(#grid)"/>
       </svg>
     </div>

     <div style="margin: 5mm; font-style: italic;">
       <p style="font-size: 18pt; font-weight: bold;
                 margin: 0;">
         {{ day }}
       </p>
       <p style="font-size: 12pt; margin: 0;">
         {{ month }}
       </p>
       <p style="font-size: 10pt; margin: 0; opacity: 0.75; color: {{- day_color(day) }};">
         {{ day.weekday }}
       </p>
     </div>
   </div>
   %% endfor

The SVG element draws a square grid with 5 mm cells. The ``<pattern>`` defines
one cell and the ``<rect>`` tiles it across the content area (with padding
around the edges). The ``back`` class stretches the SVG to fill the page, and
``z-index: -1`` puts it behind the day header.

Because ``month`` is already set to January at the top of the template,
``month.days`` gives us all 31 days. The month name is printed dynamically with
``{{ month }}`` so if you change which month the planner covers the day pages
update automatically.

Regenerate::

    pyplaner --html pages/mini-planner.html

You should see 33 pages: 1 cover + 1 month calendar + 31 day pages.
Each day page has a square grid background and a header with the day
number, month name and weekday.

.. image:: ../images/mini-planner-day-page.png
   :width: 60%
   :align: center


What is next
------------

Continue to :doc:`live-preview` to learn how to use VS Code Live Server for a
faster edit-preview workflow.

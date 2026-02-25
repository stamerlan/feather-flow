Feather Flow is a digital planner PDF generator built on top of
`Jinja2 <https://jinja.palletsprojects.com/>`_ templates and
`Playwright <https://playwright.dev/python/>`_. Design your planner pages in
HTML/CSS, feed them to **pyplaner**, and get a print-ready PDF.

|cover| |year| |month| |day|

.. |cover| image:: docs/images/cover-page.png
   :width: 24%
.. |year| image:: docs/images/year-calendar-page.png
   :width: 24%
.. |month| image:: docs/images/month-calendar-page.png
   :width: 24%
.. |day| image:: docs/images/day-page.png
   :width: 24%

Getting Started
---------------

Clone the repository::

    git clone https://github.com/stamerlan/feather-flow.git
    cd feather-flow

Install from source in a virtual environment::

    python -m venv .venv
    .venv\Scripts\activate        # Windows
    # source .venv/bin/activate   # Linux / macOS

    pip install .

Playwright requires a browser binary. Install it once after the package is
installed::

    playwright install chromium

To enable PDF optimization, install the optional ``pikepdf`` extra::

    pip install .[pikepdf]

Usage
-----

Generate a PDF from a template::

    pyplaner pages/ff-2026.html

Generate both HTML and PDF::

    pyplaner --html --pdf pages/ff-2026.html

Suppress progress output::

    pyplaner -q pages/ff-2026.html

Run ``pyplaner --help`` for the full list of options.

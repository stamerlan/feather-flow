Building the Documentation
==========================

The documentation is built with `Sphinx <https://www.sphinx-doc.org/>`_ using
the `Read the Docs <https://sphinx-rtd-theme.readthedocs.io/>`_ theme.

Prerequisites
-------------

Install the development dependencies (includes Sphinx and the theme)::

    pip install -e .[dev]

Building locally
----------------

On **Linux / macOS**::

    make -C docs html

On **Windows**::

    cd docs
    make.bat html

The generated site is written to ``docs/_build/html/``. Open
``docs/_build/html/index.html`` in a browser to view it.

To rebuild from scratch (useful after structural changes)::

    make -C docs clean html

Sphinx configuration
--------------------

The configuration lives in ``docs/conf.py``. Notable settings:

**Extensions:**

- ``sphinx.ext.autodoc`` - pulls docstrings from Python source files into the
   documentation via ``.. autoclass::`` and ``.. autofunction::`` directives.
- ``sphinx.ext.intersphinx`` - cross-references to the Python standard library
  documentation (e.g. ``:class:`~types.SimpleNamespace``` links to the stdlib
  docs).

**``sys.path`` insertion:**

``docs/conf.py`` adds ``src/`` to ``sys.path`` so that autodoc can import the
``pyplanner`` package without requiring it to be installed into the Sphinx build
environment.

Image mirroring
^^^^^^^^^^^^^^^

``README.rst`` references images as ``docs/images/*`` (correct when viewed from
the repository root on GitHub). When Sphinx includes ``README.rst`` from
``docs/index.rst`` it resolves paths relative to ``docs/``, looking for
``docs/docs/images/*``.

To satisfy both contexts, ``conf.py`` mirrors ``docs/images/`` to
``docs/docs/images/`` at build time using ``shutil.copytree()``. The mirror
directory is in ``.gitignore``.

Documentation structure
-----------------------

::

    docs/
      index.rst               Root (includes README.rst)
      conf.py                 Sphinx configuration
      Makefile                Unix build targets
      make.bat                Windows build targets
      designer-guide/         Template design tutorial
        intro.rst
        project-structure.rst
        template-basics.rst
        ...
      developer-guide/        Using pyplanner as a library
        intro.rst
        calendar-and-days.rst
        holidays.rst
        ...
      internals/              Contributing to pyplanner
        intro.rst
        project-layout.rst
        testing.rst
        ...

Each section has an ``intro.rst`` with a ``toctree`` that chains its sub-pages.
The top-level ``index.rst`` links to each section's intro, creating a
three-level hierarchy that reads top to bottom.

Autodoc conventions
-------------------

The documentation follows a "narrative first, API reference at the bottom"
pattern. Each chapter in the developer guide opens with explanatory prose and
code examples, then ends with an API reference section that uses autodoc
directives to pull in docstrings from the source.

This means most documentation lives in the source files as docstrings (Sphinx
``:param:``, ``:returns:``, ``:raises:`` fields), while the RST files provide
the narrative glue and examples.

When adding a new public class or function:

1. Write a docstring in the source file.
2. Add a ``.. autoclass::`` or ``.. autofunction::`` directive in the
   appropriate RST chapter's API reference section.
3. If the class or function introduces a new concept, add explanatory prose and
   examples above the API reference.

Deploying to GitHub Pages
-------------------------

The ``build-sphinx-docs.yml`` workflow runs on every push to ``main``. It builds
the HTML documentation and deploys it to GitHub Pages automatically. No manual
deployment is needed.

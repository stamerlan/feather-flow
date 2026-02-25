# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import shutil

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Feather Flow'
copyright = '2026, Vlad Vovchenko'
author = 'Vlad Vovchenko'
release = '1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = []

templates_path = ['_templates']
exclude_patterns = ['html', 'Thumbs.db', '.DS_Store', 'docs']



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'

# README.rst references images as docs/images/* (correct when viewed from the
# repository root, e.g. on GitHub).  When Sphinx includes README.rst from
# docs/index.rst it resolves paths relative to docs/, looking for
# docs/docs/images/*.  Mirror the images so both contexts find them.
_confdir = os.path.dirname(os.path.abspath(__file__))
_mirror = os.path.join(_confdir, 'docs', 'images')
if not os.path.exists(_mirror):
    os.makedirs(os.path.join(_confdir, 'docs'), exist_ok=True)
    shutil.copytree(os.path.join(_confdir, 'images'), _mirror)

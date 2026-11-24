# -*- coding: utf-8 -*-
#
# sqlkit documentation build configuration file.
#
# Modern Sphinx configuration using the pydata-sphinx-theme.

import os
import sys

# Make the local docusage extension and the sqlkit package importable.
cur_dir = os.path.dirname(__file__)
sys.path += [cur_dir]
sys.path += [os.path.dirname(cur_dir)]

import sqlkit

# -- Project information -----------------------------------------------------

project = 'sqlkit'
copyright = '2008-2025, Sandro Dentella'
author = 'Sandro Dentella'

# The full version, including alpha/beta/rc tags.
release = '1.2.0'
# The short X.Y version.
version = '1.2.0'

# -- General configuration ---------------------------------------------------

extensions = [
    'sphinx.ext.autodoc',
    'docusage',
]

source_suffix = '.rst'

# The master toctree document / homepage.
root_doc = 'index'

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# -- Options for HTML output -------------------------------------------------

html_theme = 'pydata_sphinx_theme'

# The logo (284x106 px, fits the navbar nicely).
html_logo = 'static/sqlkit.png'

html_static_path = ['static']

html_theme_options = {
    'navbar_align': 'left',
    'show_prev_next': True,
    'footer_start': ['copyright'],
    'footer_end': ['theme-version'],
    # Top-level navbar sections (mirrors the legacy live site navigation).
    'header_links_before_dropdown': 6,
}

# If not '', a 'Last updated on:' timestamp is inserted at every page bottom.
html_last_updated_fmt = '%b %d, %Y'

# Output file base name for HTML help builder.
htmlhelp_basename = 'sqlkitdoc'

# -- Options for LaTeX output ------------------------------------------------

latex_documents = [
    ('index', 'sqlkit.tex', 'sqlkit Documentation', 'Sandro Dentella', 'manual'),
]

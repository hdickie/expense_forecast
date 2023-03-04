# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'expense_forecast'
copyright = '2022, Hume Dickie'
author = 'Hume Dickie'
release = '0.0.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = []

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']

extensions = ['sphinx.ext.autodoc','sphinxjp.themes.basicstrap']

import os
import sys
sys.path.insert(0, os.path.abspath('.'))

html_theme = "classic"
html_theme_path = ["."]

html_theme_options = {
    'sidebarwidth': 400
} #When I put this in classic.css, classic.css gets overwritten every time I use "make html"

autoclass_content = 'both'
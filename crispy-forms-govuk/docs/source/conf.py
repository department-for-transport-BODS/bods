# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys

from django.conf import settings  # noqa: F401

sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("../../"))

os.environ["DJANGO_SETTINGS_MODULE"] = "dummy_settings"


# -- Project information -----------------------------------------------------

project = "crispy-forms-govuk"
copyright = "2019, Greg Brown"
author = "Greg Brown"

# The full version, including alpha/beta/rc tags
release = "0.1"


# -- General configuration ---------------------------------------------------
master_doc = "index"  # fix issue https://github.com/rtfd/readthedocs.org/issues/2569#issuecomment-485117471

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = ["sphinx.ext.autodoc", "sphinx.ext.napoleon"]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "alabaster"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

# Napoleon
# http://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html#configuration
napoleon_use_admonition_for_notes = False

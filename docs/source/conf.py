# -*- coding: utf-8 -*-

import os
import sys
import sphinx_rtd_theme
sys.path.insert(0, os.path.abspath('../../'))

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinx.ext.viewcode',
    'sphinx.ext.autosectionlabel',
    'sphinx_rtd_theme',
]

templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'

project = u'PyANCP'
copyright = u'Copyright 2017-2024, Christian Giese (GIc-de)'
author = u'Christian Giese'
version = u'0.1'
release = u'0.1.8'

language = 'en'
exclude_patterns = []

pygments_style = 'sphinx'

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

htmlhelp_basename = 'PyANCPdoc'

intersphinx_mapping = {'https://docs.python.org/': None}

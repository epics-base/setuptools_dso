import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

project = u'setuptools_dso'
copyright = u'2021, Michael Davidsaver'

master_doc = 'index'

extensions = [
    'sphinx.ext.autodoc',
]

#default_role = "any"

html_theme = 'alabaster'

html_theme_options = {
    'page_width': '1200px',   # better on my 8/5 ratio screen
    'sidebar_width': '270px', # avoid wrapping 'setuptools_dso' at top of sidebar
    'github_banner': True,
    'github_button': True,
    'github_user': 'mdavidsaver',
    'github_repo': 'setuptools_dso',
}

"""
This extension defines the 'translation-warning' directive, that is displayed
only when a page is older than the one it is supposed to be a translation of.
"""

from sphinx.application import Sphinx

from .directives import setup as setup_directives
from .config import setup as setup_config
from .handlers import setup as setup_handlers

#############################################################
# Setup

def setup(app: Sphinx):
    setup_config(app)

    setup_directives(app)

    setup_handlers(app)

    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }

from typing import Dict, Any
from os.path import dirname, join

from sphinx.application import Sphinx
from sphinx.locale import _
from sphinx.util.fileutil import copy_asset_file
from sphinx.environment.adapters.toctree import TocTree

from .utils import print_traceback

from docutils import nodes
from sphinx.errors import ExtensionError

####################################################

@print_traceback
def on_env_purge_doc(app: Sphinx, env, docname: str):
    pass

####################################################

@print_traceback
def on_env_merge_info(app, env, docnames, other):
    pass

####################################################

@print_traceback
def on_doctree_resolved(app: Sphinx, doctree, fromdocname: str):
    pass

####################################################

@print_traceback
def on_build_finished(app: Sphinx, exc):
    asset_files = [
        "css/diff-admonition.css",
        "css/translation.css",
        "js/diff-admonition.js",
    ]
    if app.builder.format == 'html' and not exc:
        staticdir = join(app.builder.outdir, '_static')
        root = dirname(__file__)
        for path in asset_files:
            copy_asset_file(join(root, path), staticdir)

#############################################################

@print_traceback
def on_html_page_context(
    app: Sphinx,
    docname: str,
    templatename: str,
    context: Dict[str, Any],
    doctree: Any,
):
    pass

#############################################################
# Setup

def setup(app):
    app.connect('doctree-resolved', on_doctree_resolved)
    app.connect('env-purge-doc', on_env_purge_doc)
    app.connect('env-merge-info', on_env_merge_info)
    app.connect('build-finished', on_build_finished)
    app.connect('html-page-context', on_html_page_context)

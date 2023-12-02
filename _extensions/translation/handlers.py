from typing import Dict, Any
from os.path import dirname, join

from sphinx.application import Sphinx
from sphinx.locale import _
from sphinx.util.fileutil import copy_asset_file
from sphinx.environment.adapters.toctree import TocTree
from sphinx import addnodes
from sphinx.environment.adapters.toctree import _resolve_toctree, _get_toctree_ancestors

from sphinx.environment import BuildEnvironment
from sphinx.builders import Builder
from docutils.nodes import Element

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

def get_local_toctree_no_toplevel(builder: Builder, docname: str, collapse: bool = True, **kwargs: Any) -> str:
    """Variant from sphinx.builders.html.__init__ that calls toctree_for_doc_no_toplevel"""
    if 'includehidden' not in kwargs:
        kwargs['includehidden'] = False
    if kwargs.get('maxdepth') == '':
        kwargs.pop('maxdepth')
    toctree = toctree_for_doc_no_toplevel(builder.env, docname, builder, collapse=collapse, **kwargs)
    return builder.render_partial(toctree)['fragment']

def toctree_for_doc_no_toplevel(
    env: BuildEnvironment,
    docname: str,
    builder: Builder,
    collapse: bool = False,
    includehidden: bool = True,
    maxdepth: int = 0,
    titles_only: bool = False,
) -> Element | None:
    """Variant of environment.adapters.toctree that does not return the top level
    """

    # Find ancestor that serves as sub root
    all_ancestors = list(_get_toctree_ancestors(env.toctree_includes, docname))
    if all_ancestors:
        ancestor = all_ancestors[-1]
    else:
        ancestor = env.config.root_doc

    toctrees: list[Element] = []
    for toctree_node in env.get_doctree(ancestor).findall(addnodes.toctree):
        if toctree := _resolve_toctree(
            env,
            docname,
            builder,
            toctree_node,
            prune=True,
            maxdepth=int(maxdepth),
            titles_only=titles_only,
            collapse=collapse,
            includehidden=includehidden,
        ):
            toctrees.append(toctree)
    if not toctrees:
        return None
    result = toctrees[0]
    for toctree in toctrees[1:]:
        result.extend(toctree.children)
    return result

@print_traceback
def on_html_page_context(
    app: Sphinx,
    docname: str,
    templatename: str,
    context: Dict[str, Any],
    doctree: Any,
):
    context["toctree"] = lambda **kwargs: get_local_toctree_no_toplevel(app.builder, docname, **kwargs)

#############################################################

@print_traceback
def on_doctree_read(app, doctree):
    print("################### on_doctree_read")
    print(dir(doctree))
    doctree["source"] = doctree["source"].replace("translation\\", "")
    print(doctree["source"])

#############################################################
# Setup

def setup(app):
    #app.connect('config-inited', on_config_inited)
    #app.connect('doctree-resolved', on_doctree_resolved)
    #app.connect('env-purge-doc', on_env_purge_doc)
    #app.connect('env-merge-info', on_env_merge_info)
    app.connect('build-finished', on_build_finished)
    app.connect('html-page-context', on_html_page_context)
    #app.connect('doctree-read', on_doctree_read)

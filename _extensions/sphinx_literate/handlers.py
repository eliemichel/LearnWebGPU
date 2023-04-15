from typing import Dict, Any
from os.path import dirname, join

from sphinx.application import Sphinx
from sphinx.locale import _
from sphinx.util.fileutil import copy_asset_file
from sphinx.environment.adapters.toctree import TocTree

from .registry import CodeBlock, CodeBlockRegistry
from .nodes import LiterateNode, TangleNode, RegistryNode
from .tangle import tangle
from .utils import print_traceback

from docutils import nodes

####################################################

@print_traceback
def purge_registry(app: Sphinx, env, docname: str):
    registry = CodeBlockRegistry.from_env(env)
    registry.remove_codeblocks_by_docname(docname)

####################################################

@print_traceback
def merge_registry(app, env, docnames, other):
    registry = CodeBlockRegistry.from_env(env)
    registry.merge(CodeBlockRegistry.from_env(other))

####################################################

@print_traceback
def process_literate_nodes(app: Sphinx, doctree, fromdocname: str):
    registry = CodeBlockRegistry.from_env(app.builder.env)
    registry.check_integrity()

    has_literate_node = False
    for literate_node in doctree.findall(LiterateNode):
        has_literate_node = True
        literate_node.uid_to_lit = {
            uid: (registry.get_rec_by_key(link.key), link.options)
            for uid, link in literate_node.uid_to_block_link.items()
        }
        literate_node.references = [
            registry.get_by_key(k)
            for k in registry.references_to_key(literate_node.lit.key)
        ]

        # Fix references broken by serialization
        literate_node.lit = registry.get_by_uid(literate_node.lit.uid)

    for tangle_node in doctree.findall(TangleNode):

        tangled_content, lit = tangle(
            tangle_node.block_name,
            tangle_node.tangle_root,
            registry,
            app.config,
            f"in tangle directive from {tangle_node.source_location.format()}, "
        )

        para = nodes.paragraph()
        para += nodes.Text(f"Tangled block '{lit.name}' [from ")

        refnode = nodes.reference('', '')
        refnode['refdocname'] = lit.source_location.docname
        refnode['refuri'] = lit.link_url(fromdocname, app.builder)
        refnode.append(nodes.emphasis(_('here'), _('here')))
        para += refnode
        
        para += nodes.Text("]")

        lexer = tangle_node.lexer
        if lexer is None:
            lexer = lit.lexer

        block_node = tangle_node.raw_block_node
        block_node.args = [lexer] if lexer is not None else []
        block_node.rawsource = '\n'.join(tangled_content)
        if lexer is not None:
            block_node['language'] = lexer
        block_node.children.clear()
        block_node.children.append(nodes.Text(block_node.rawsource))

        tangle_node.replace_self([para, block_node])

    # For each document, we tell whether it contains at least one lit block
    # (to be able to show literate options conditionally)
    if not hasattr(app.builder.env, 'lit_doc_contains_block'):
        app.builder.env.lit_doc_contains_block = {}
    app.builder.env.lit_doc_contains_block[fromdocname] = has_literate_node

    registry_dump = registry.pretty_dump()
    for registry_node in doctree.findall(RegistryNode):
        block_node = registry_node.raw_block_node
        block_node.rawsource = '\n'.join(registry_dump)
        block_node.children.clear()
        block_node.children.append(nodes.Text(block_node.rawsource))
        registry_node.replace_self([block_node])

####################################################

@print_traceback
def copy_custom_files(app: Sphinx, exc):
    if app.config.lit_use_default_style:
        asset_files = [
            "js/sphinx_literate.js",
        ]
    else:
        asset_files = []
    if app.builder.format == 'html' and not exc:
        staticdir = join(app.builder.outdir, '_static')
        root = dirname(__file__)
        for path in asset_files:
            copy_asset_file(join(root, path), staticdir)

#############################################################

@print_traceback
def html_page_context(
    app: Sphinx,
    docname: str,
    templatename: str,
    context: Dict[str, Any],
    doctree: Any,
):
    builder = app.builder
    #toctree = TocTree(builder.env).get_toc_for(docname, builder)
    #found_lit_block = list(toctree.findall(LiterateNode)) != []
    found_lit_block = builder.env.lit_doc_contains_block.get(docname, False)
    context["lit_show_options"] = found_lit_block

#############################################################
# Setup

def setup(app):
    app.connect('doctree-resolved', process_literate_nodes)
    app.connect('env-purge-doc', purge_registry)
    app.connect('env-merge-info', merge_registry)
    app.connect('build-finished', copy_custom_files)
    app.connect('html-page-context', html_page_context)

from typing import Dict, Any, List, Tuple
from os.path import dirname, join
from dataclasses import dataclass

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

def get_local_master(env: BuildEnvironment, docname: str):
    """Return the name of the document used as master root for a given doc"""
    all_ancestors = list(_get_toctree_ancestors(env.toctree_includes, docname))
    if all_ancestors:
        return all_ancestors[-1]
    else:
        return env.config.root_doc

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
    """Variant of environment.adapters.toctree that does not return the top level"""

    # Find ancestor that serves as sub root
    ancestor = get_local_master(env, docname)

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

@dataclass
class TranslationMetadata:
    is_current: bool
    language_emoji: str
    language_name: str
    language_name_en: str
    translated_docname: str

def get_translation(
    env: BuildEnvironment,
    docname_default: str,
    language_info: Tuple[str, str, str, str],
    current_lang: str,
    default_lang: str,
) -> TranslationMetadata | None:
    short_language_name, language_emoji, language_name, language_name_en = language_info
    is_current = short_language_name == current_lang
    if short_language_name != default_lang:
        translated_docname = f"{short_language_name}/{docname_default}"
    else:
        translated_docname = docname_default

    try:
        env.get_doctree(translated_docname)
    except FileNotFoundError:
        return None

    return TranslationMetadata(
        is_current,
        language_emoji,
        language_name,
        language_name_en,
        translated_docname
    )

def get_all_translations(
    env: BuildEnvironment,
    docname: str,
    translation_languages: List[Tuple[str, str, str, str]],
) -> List[TranslationMetadata]:
    default_lang = "en"
    current_lang = None
    for lang in translation_languages:
        short_language_name = lang[0]
        if docname.startswith(f"{short_language_name}/"):
            current_lang = short_language_name

    if current_lang is None:
        current_lang = default_lang
        docname_default = docname
    else:
        # Remove language prefix
        docname_default = docname[len(current_lang)+1:]

    all_translations = []
    for lang in translation_languages:
        if tr := get_translation(env, docname_default, lang, current_lang, default_lang):
            all_translations.append(tr)
    return all_translations

@print_traceback
def on_html_page_context(
    app: Sphinx,
    docname: str,
    templatename: str,
    context: Dict[str, Any],
    doctree: Any,
):
    builder = app.builder
    env = builder.env

    context["toctree"] = lambda **kwargs: get_local_toctree_no_toplevel(builder, docname, **kwargs)
    context["master_doc"] = get_local_master(env, docname)
    context["translations"] = get_all_translations(env, docname, app.config.translation_languages)

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

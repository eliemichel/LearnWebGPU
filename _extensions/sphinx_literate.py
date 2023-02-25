"""
sphinx_literate is an extension inspired by the concept of Literate Programming

It provides a directive close to code blocks, called `lit`. The author can
specify how these literate code blocks should be assembled together in order to
produce the full code that is presented in the documentation.

Let's take a very simple example:

```{lit} Base skeleton
#include <iostream>
int main(int, char**) {
    {{Main content}}
}
```

And we can later define the main content:

```{lit} C++, Main content
std::cout << "Hello world" << std::endl;
```

This naming provides 2 complementzary features:

 1. The documentation's source code can be transformed into a fully working
    code. This is traditionnaly called the **tangled** code.

 2. The documentation can display links that help navigating through the code
    even though the documentation presents it non-linearily.

**NB** The syntax for referencing other code blocks is `<<Some block name>>`
by default, but as this may conflict with the syntax of your programming
language, you can customize it with the options `lit_begin_ref` and
`lit_end_ref`.

**NB** The language lexer name (C++ in the example above) is optional, and
provided as a first token separated from the block name by a comma (,).

"""

from docutils import nodes
from docutils.parsers import rst
from docutils.parsers.rst import Directive
from docutils.statemachine import StringList, State, StateMachine

import sphinx
from sphinx.locale import _
from sphinx.util.docutils import SphinxDirective
from sphinx.errors import ExtensionError
from sphinx.directives.code import CodeBlock as SphinxCodeBlock

from dataclasses import dataclass
from typing import Any
from copy import deepcopy
import re

#############################################################
# Codeblock registry

@dataclass
class Codeblock:
    """
    Data store about a code block parsed from a {lit} directive, to be
    assembled when tangling.
    """
    name: str = ""
    docname: str = ""
    lineno: int = -1
    content: str = ""
    target: Any = None

    @property
    def key(self):
        # TODO: Add config option to scope blocks per document
        return self.name

class CodeblockRegistry:
    """
    Holds the various code blocks and prevents duplicates.
    NB: Do not create this yourself, call CodeblockRegistry.from_env(env)
    """

    @classmethod
    def from_env(cls, env):
        if not hasattr(env, 'lit_codeblocks'):
            env.lit_codeblocks = CodeblockRegistry()
        return env.lit_codeblocks

    def __init__(self):
        self._blocks = {}

    def add_codeblock(self, lit: Codeblock):
        key = lit.key
        existing = self._blocks.get(key)
        if existing is not None:
            message = (
                f"Multiple literate code blocks with the same name '{key}' were found:\n" +
                f"  - In document '{existing.docname}', line {existing.lineno}.\n"
                f"  - In document '{lit.docname}', line {lit.lineno}.\n"
            )
            raise ExtensionError(message, modname="sphinx_literate")
        self._blocks[key] = lit

    def remove_codeblocks_by_docname(self, docname):
        self._blocks = {
            key: lit
            for key, lit in self._blocks.items()
            if lit.docname != docname
        }

    def blocks(self):
        return self._blocks.values()

    def get(self, key):
        return self._blocks.get(key)

#############################################################
# Elements

# This is totally a hack for being able to call SphinxDirectives from
# the doctree-resolved event callback.
class MockReporter:
    pass
class MockStateMachine:
    def __init__(self, document):
        self.document = document
        self.reporter = document.reporter
    def get_source_and_line(self, lineno = None):
        return self.document["source"], lineno or 0
class MockState:
    def __init__(self, state_machine):
        self.document = state_machine.document

class tangle_node(nodes.General, nodes.Element):
    def __init__(self, root_block_name, lexer, docname, lineno, state_machine_proto, state_proto, *args):
        self.lexer = lexer
        self.root_block_name = root_block_name
        self.docname = docname
        self.lineno = lineno

        self._document = state_machine_proto.document

        super().__init__(*args)

    def state_machine_factory(self):
        return MockStateMachine(self._document)

    def state_factory(self, state_machine):
        #state = deepcopy(self._state_proto)
        #state.state_machine = state_machine
        return MockState(state_machine)

class literate_node(nodes.General, nodes.Element):
    pass

#############################################################
# Tangle

def tangle(registry, tangled_content, lit_content, begin_ref, end_ref, prefix=""):
    for line in lit_content:
        subprefix = None
        key = None
        begin_offset = line.find(begin_ref)
        if begin_offset != -1:
            end_offset = line.find(end_ref, begin_offset)
            if end_offset != -1:
                subprefix = line[:begin_offset]
                key = line[begin_offset+2:end_offset]
        if key is not None:
            sublit = registry.get(key)
            if sublit is None:
                message = (
                    f"Literate code block not found: '{key}' " +
                    f"(in tangle directive from document {node.docname}, line {node.lineno})"
                )
                raise ExtensionError(message, modname="sphinx_literate")
            tangle(
                registry,
                tangled_content,
                sublit.content,
                begin_ref,
                end_ref,
                prefix=prefix + subprefix
            )
        else:
            tangled_content.append(prefix + line)

#############################################################
# Directives

class DirectiveMixin:
    def parse_arguments(self):
        self.arg_lexer = None
        self.arg_name = ""

        raw_args = self.arguments[0]
        tokens = raw_args.split(",")
        if len(tokens) == 1:
            self.arg_name = tokens[0]
        elif len(tokens) == 2:
            self.arg_lexer = tokens[0].strip()
            self.arg_name = tokens[1].strip()
        else:
            message = (
                f"Invalid block name: '{raw_args}'\n" +
                "At most 1 comma is allowed, to specify the language, but the name cannot contain a comma."
            )
            raise ExtensionError(message, modname="sphinx_literate")

class TangleDirective(SphinxDirective, DirectiveMixin):

    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True

    def run(self):
        self.parse_arguments()
        return [tangle_node(
            self.arg_name,
            self.arg_lexer,
            self.env.docname,
            self.lineno,
            self.state_machine,
            self.state
        )]

class LiterateDirective(SphinxCodeBlock, DirectiveMixin):

    has_content = True
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True

    def run(self):
        self.parse_arguments()

        targetid = 'lit-%d' % self.env.new_serialno('lit')
        targetnode = nodes.target('', '', ids=[targetid])

        self.register_lit(targetnode)

        # Call parent for generating a regular code block
        text = '\n'.join(self.content)
        # TODO: process text here?
        text = f"// {self.arg_name}:\n" + text
        self.content = StringList(text.split('\n'))

        self.arguments = [self.arg_lexer] if self.arg_lexer is not None else []

        out_nodes = super().run()

        return [targetnode, *out_nodes]

    def register_lit(self, targetnode):
        lit_codeblocks = CodeblockRegistry.from_env(self.env)

        lit_codeblocks.add_codeblock(Codeblock(
            name=self.arg_name,
            docname=self.env.docname,
            lineno=self.lineno,
            content=self.content,
            target=targetnode,
        ))

def purge_lit_codeblocks(app, env, docname):
    lit_codeblocks = CodeblockRegistry.from_env(env)
    lit_codeblocks.remove_codeblocks_by_docname(docname)

def merge_lit_codeblocks(app, env, docnames, other):
    lit_codeblocks = CodeblockRegistry.from_env(env)

    for lit in CodeblockRegistry.from_env(other).blocks():
        lit_codeblocks.add_codeblock(lit)

def process_literate_nodes(app, doctree, fromdocname):
    lit_codeblocks = CodeblockRegistry.from_env(app.builder.env)

    for node in doctree.findall(tangle_node):
        content = []
        lit = lit_codeblocks.get(node.root_block_name)
        if lit is not None:
            para = nodes.paragraph()
            para += nodes.Text(f"Tangled block '{lit.name}' [from ")

            refnode = nodes.reference('', '')
            refnode['refdocname'] = lit.docname
            refnode['refuri'] = (
                app.builder.get_relative_uri(fromdocname, lit.docname)
                + '#' + lit.target['refid']
            )
            refnode.append(nodes.emphasis(_('here'), _('here')))
            para += refnode
            
            para += nodes.Text("]")

            content.append(para)

            tangled_content = []
            tangle(
                lit_codeblocks,
                tangled_content,
                lit.content,
                app.config.lit_begin_ref,
                app.config.lit_end_ref,
            )

            state_machine = node.state_machine_factory()
            state = node.state_factory(state_machine)
            code_block = SphinxCodeBlock(
                "", # name
                [node.lexer],  # arguments
                {},  # options
                tangled_content,  # content
                0,  # lineno
                0,  # content_offset
                "",  # block_text
                state,  # state
                state_machine,  # state_machine
            ).run()[0]
            content.append(code_block)

        node.replace_self(content)

def setup(app):
    app.add_config_value("lit_begin_ref", "<<", 'html', [str])
    app.add_config_value("lit_end_ref", ">>", 'html', [str])

    app.add_node(tangle_node)
    #app.add_node(literate_node)

    app.add_directive("tangle", TangleDirective)
    app.add_directive("lit", LiterateDirective)

    app.connect('doctree-resolved', process_literate_nodes)
    app.connect('env-purge-doc', purge_lit_codeblocks)
    app.connect('env-merge-info', merge_lit_codeblocks)

    return {
        'version': '0.2',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }

from typing import List

from docutils import nodes
from docutils.nodes import Node, Element
from docutils.parsers.rst import directives
from docutils.statemachine import StringList

from sphinx.util.docutils import SphinxDirective
from sphinx.util.typing import OptionSpec
from sphinx.directives.code import CodeBlock as SphinxCodeBlock
from sphinx.application import Sphinx

from .parse import parse_block_content, parse_block_title, parse_fetched_files
from .registry import CodeBlock, CodeBlockRegistry, SourceLocation
from .nodes import LiterateNode, TangleNode, RegistryNode

#############################################################

class LiterateSetupDirective(SphinxDirective):
    """
    Directive to set local options for sphinx_literate.
    """

    has_content = False
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec: OptionSpec = {
        'force': directives.flag,
        'linenothreshold': directives.positive_int,
        'tangle-root': directives.unchanged,
        'parent': directives.unchanged,
        'fetch-files': directives.unchanged,
    }

    def run(self) -> List[Node]:
        tangle_root = self.options.get('tangle-root')
        tangle_parent = self.options.get('parent')
        fetch_files = self.options.get('fetch-files')
        force = 'force' in self.options
        reg = CodeBlockRegistry.from_env(self.env)

        if tangle_root is not None:
            self.env.temp_data['tangle-root'] = tangle_root
        else:
            tangle_root = self.env.temp_data['tangle-root']

        if tangle_parent is not None:
            reg.set_tangle_parent(
                tangle_root,
                tangle_parent,
                SourceLocation(
                    docname = self.env.docname,
                    lineno = self.lineno,
                ),
                parse_fetched_files(fetch_files, self.env.docname),
            )

        return []

#############################################################

class TangleDirective(SphinxCodeBlock):

    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True

    def run(self):
        parsed_title = parse_block_title(self.arguments[0])
        tangle_root = self.env.temp_data.get('tangle-root')

        self.content = StringList(["Hello, world"])
        self.arguments = [parsed_title.lexer] if parsed_title.lexer is not None else []

        raw_block_node = super().run()[0]

        return [
            TangleNode(
                parsed_title.name,
                tangle_root,
                parsed_title.lexer,
                SourceLocation(
                    docname = self.env.docname,
                    lineno = self.lineno,
                ),
                raw_block_node,
            )
        ]

#############################################################

class RegistryDirective(SphinxCodeBlock):
    """
    This is close to the tangle directive, in the fact that it creates a code
    block that will be populated only.
    """

    required_arguments = 0
    optional_arguments = 0

    def run(self):
        raw_block_node = super().run()[0]

        return [
            RegistryNode(
                SourceLocation(
                    docname = self.env.docname,
                    lineno = self.lineno,
                ),
                raw_block_node,
            )
        ]

#############################################################

class LiterateDirective(SphinxCodeBlock):

    has_content = True
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True

    def run(self):
        tangle_root = self.env.temp_data.get('tangle-root')
        parsed_title = parse_block_title(self.arguments[0])
        self.parsed_content = parse_block_content(self.content, tangle_root, self.config)

        targetid = 'lit-%d' % self.env.new_serialno('lit')
        targetnode = nodes.target('', '', ids=[targetid])

        self.lit = CodeBlock(
            name = parsed_title.name,
            tangle_root = tangle_root,
            source_location = SourceLocation(
                docname = self.env.docname,
                lineno = self.lineno,
            ),
            content = self.content,
            target = targetnode,
            lexer = parsed_title.lexer,
        )

        lit_codeblocks = CodeBlockRegistry.from_env(self.env)
        lit_codeblocks.register_codeblock(self.lit, parsed_title.options)
        
        for ref in self.parsed_content.uid_to_block_link.values():
            lit_codeblocks.add_reference(self.lit.key, ref.key)

        # Call parent for generating a regular code block
        self.content = StringList(self.parsed_content.content)
        self.arguments = [parsed_title.lexer] if parsed_title.lexer is not None else []

        block_node = self.create_block_node()

        return [targetnode, block_node]

    def create_block_node(self):
        """
        Call parent class' run to create a code block, and post process it to
        inject our literate code block.
        """
        raw_block_node = super().run()[0]

        if isinstance(raw_block_node, nodes.literal_block):
            block_node = nodes.container(classes=['literal-block-wrapper'])
            block_node += self.wrap_literal_node(raw_block_node)
        else:
            new_children = []
            for node in raw_block_node:
                if isinstance(node, nodes.literal_block):
                    node = self.wrap_literal_node(node)
                new_children.append(node)
            block_node = raw_block_node
            block_node.children = new_children

        block_node['classes'].append("lit-block-wrapper")
        if self.lit.hidden:
            block_node['classes'].append("lit-block-hidden")
        return block_node

    def wrap_literal_node(self, raw_literal_node):
        """
        Wrap Sphinx literal node with our literate node, which contains context
        about what reference links to insert during the final translation.
        """
        literate_node = LiterateNode(raw_literal_node, self.lit)
        literate_node.uid_to_block_link = self.parsed_content.uid_to_block_link
        return literate_node

#############################################################

def setup(app: Sphinx) -> None:
    app.add_directive("lit-setup", LiterateSetupDirective)
    app.add_directive("lit", LiterateDirective)
    app.add_directive("lit-registry", RegistryDirective)
    app.add_directive("tangle", TangleDirective)

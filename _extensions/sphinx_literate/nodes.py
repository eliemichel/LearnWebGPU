from docutils import nodes

import html
import json

from .registry import Key, CodeBlock, SourceLocation

#############################################################

class TangleNode(nodes.General, nodes.Element):
    def __init__(self, block_name, tangle_root, lexer, source_location, raw_block_node, *args):
        self.block_name = block_name
        self.tangle_root = tangle_root
        self.lexer = lexer
        self.source_location = source_location
        self.raw_block_node = raw_block_node

        super().__init__(*args)

#############################################################

class LiterateHighlighter:
    """
    A custom code block highlighter that uses an existing highlighter and
    insert custom links for references to other code blocks
    """
    def __init__(self, original_highlighter, node, ref_factory):
        self._original_highlighter = original_highlighter
        self.node = node
        self.ref_factory = ref_factory

    def highlight_block(self, rawsource, lang, **kwargs):
        # Pre-process is done by the LiterateDirective

        highlighted = self._original_highlighter.highlight_block(rawsource, lang, **kwargs)

        # Post-process: Replace hashes with links
        for uid, lit in self.node.uid_to_lit.items():
            ref = self.ref_factory(self.node, lit)
            highlighted = highlighted.replace(uid, ref)

        return highlighted

#############################################################

class LiterateNode(nodes.General, nodes.Element):
    def __init__(self, literal_node, lit: CodeBlock, *args):
        """
        We wrap a literal node and insert links to references code blocks
        """
        self._literal_node = literal_node
        self.uid_to_block_key = {}
        self.uid_to_lit = {}
        self.lit = lit
        self.references: List[CodeBlock] = []
        super().__init__(*args)

    @classmethod
    def build_translation_handlers(cls, app):
        """
        This is a hack for inheriting the literal_block visitors so that we
        support as many builders as possible.
        (Feel free to suggest a better way...)
        """
        literal_block_handlers = {}
        reference_handlers = {}
        for name, builder in app.registry.builders.items():
            default = builder.default_translator_class
            translator_class = app.registry.translators.get(
                name,
                default.fget(app) if type(default) == property else default
            )
            if translator_class is None:
                continue
            literal_block_handlers[name] = (
                translator_class.visit_literal_block,
                translator_class.depart_literal_block
            )
            reference_handlers[name] = (
                translator_class.visit_reference,
                translator_class.depart_reference
            )

        inherited_html_visit, inherited_html_depart = literal_block_handlers.get('html', (None, None))

        def create_ref(node, lit):
            """
            # TODO: Could this be a way to make that protable to all builders?
            refnode = nodes.reference('', '')
            refnode['refdocname'] = lit.docname
            refnode['refuri'] = (
                app.builder.get_relative_uri(node.document['source'], lit.docname)
                + '#' + lit.target['refid']
            )
            refnode.append(nodes.Text(lit.name))
            """
            url = lit.link_url(node.lit.source_location.docname, app.builder)
            lexer = f'"{lit.lexer}"' if lit.lexer is not None else "null";
            return (
                f'<lit-ref name="{lit.name}" href="{url}" lexer={lexer}>' +
                    app.config.lit_begin_ref +
                        f'<a href="{url}">{lit.name}</a>' +
                    app.config.lit_end_ref +
                '</lit-ref>'
            )

        def visit_html(self, node):
            # Override highlighter
            original_highlighter = self.highlighter
            self.highlighter = LiterateHighlighter(original_highlighter, node, create_ref)

            # Copy anchoring properties from wrapper node to internal node
            node._literal_node['ids'] = node['ids']
            node._literal_node['names'] = node['names']
            for prop in ['expect_referenced_by_name', 'expect_referenced_by_id']:
                if hasattr(node, prop):
                    setattr(node._literal_node, prop, getattr(node, prop))

            # Call inherited visitor
            try:
                inherited_html_visit(self, node._literal_node)
                skip = False
            except nodes.SkipNode:
                skip = True
            
            # Restore highlighter
            self.highlighter = original_highlighter

            docname = node.lit.source_location.docname

            def make_link_metadata(lit):
                return {
                    'name': lit.name,
                    'url': lit.link_url(docname, self.builder),
                }

            metadata = {
                'name': node.lit.name,
                'permalink': "#" + node.lit.target['refid'],
                'replaced by': [],
                'completed in': [],
                'completing': [],
                'replacing': [],
                'referenced in': [],
            }

            if node.lit.prev is not None:
                section = {
                    'REPLACE': 'replacing',
                    'APPEND': 'completing',
                }[node.lit.relation_to_prev]
                metadata[section].append(
                    make_link_metadata(node.lit.prev)
                )

            if node.lit.next is not None:
                section = {
                    'REPLACE': 'replaced by',
                    'APPEND': 'completed in',
                }[node.lit.next.relation_to_prev]
                metadata[section].append(
                    make_link_metadata(node.lit.next)
                )

            for ref in node.references:
                metadata['referenced in'].append(
                    make_link_metadata(ref)
                )

            encoded_metadata = html.escape(json.dumps(metadata))
            self.body.append(
                f'<lit-block-info data="{encoded_metadata}"></lit-block-info>'
            )

            if skip:
                raise nodes.SkipNode

        def depart_html(self, node):
            inherited_html_depart(self, node._literal_node)

        literal_block_handlers['html'] = (
            visit_html,
            depart_html,
        )
        return literal_block_handlers

#############################################################

def setup(app):
    app.add_node(TangleNode)
    app.add_node(LiterateNode, **LiterateNode.build_translation_handlers(app))

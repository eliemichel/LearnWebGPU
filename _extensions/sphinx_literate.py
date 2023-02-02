from docutils import nodes
from docutils.parsers.rst import Directive

from sphinx.locale import _
from sphinx.util.docutils import SphinxDirective

class tangle_node(nodes.General, nodes.Element):
    pass

class literate_node(nodes.General, nodes.Element):
    pass

class TangleDirective(Directive):
    def run(self):
        return [tangle_node('')]

class LiterateDirective(SphinxDirective):

    has_content = True

    def run(self):
        targetid = 'lit-%d' % self.env.new_serialno('lit')
        targetnode = nodes.target('', '', ids=[targetid])

        self.register_lit(targetnode)

        paragraph = nodes.paragraph()
        paragraph += nodes.Text("Lit")

        return [targetnode, paragraph]

    def register_lit(self, targetnode):
        if not hasattr(self.env, 'lit_codeblocks'):
            self.env.lit_codeblocks = []

        self.env.lit_codeblocks.append({
            'docname': self.env.docname,
            'lineno': self.lineno,
            'content': self.content,
            'target': targetnode,
        })

def purge_lit_codeblocks(app, env, docname):
    if not hasattr(env, 'lit_codeblocks'):
        return

    env.lit_codeblocks = [
        lit
        for lit in getattr(env, 'lit_codeblocks', [])
        if lit['docname'] != docname
    ]

def merge_lit_codeblocks(app, env, docnames, other):
    if not hasattr(self.env, 'lit_codeblocks'):
        self.env.lit_codeblocks = []
    self.env.lit_codeblocks.extend(getattr(other, 'lit_codeblocks', []))

def process_literate_nodes(app, doctree, fromdocname):
    env = app.builder.env
    lit_codeblocks = getattr(env, 'lit_codeblocks', [])

    for node in doctree.findall(tangle_node):
        content = []
        for lit in lit_codeblocks:
            para = nodes.paragraph()
            para += nodes.Text("\n".join(lit["content"]) + "\n[from ")

            refnode = nodes.reference('', '')
            refnode['refdocname'] = lit['docname']
            refnode['refuri'] = (
                app.builder.get_relative_uri(fromdocname, lit['docname'])
                + '#' + lit['target']['refid']
            )
            refnode.append(nodes.emphasis(_('here'), _('here')))
            para += refnode
            
            para += nodes.Text("]")

            content.append(para)

        node.replace_self(content)

def setup(app):
    #app.add_config_value('lit_tangle', True, 'html')

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

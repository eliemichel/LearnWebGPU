from sphinx.highlighting import lexers
from pygments.filters import VisibleWhitespaceFilter
from pygments.lexers.compiled import CppLexer, RustLexer

def setup(app):
    """Replace tabs with 4 spaces"""
    lexers['C++'] = CppLexer()
    lexers['rust'] = RustLexer()

    ws_filter = VisibleWhitespaceFilter(tabs=' ', tabsize=4)
    for lx in lexers.values():
        lx.add_filter(ws_filter)

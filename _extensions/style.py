from sphinx.highlighting import lexers
from pygments.filters import VisibleWhitespaceFilter
from pygments.token import Keyword, Name, String
from pygments.lexers.compiled import CppLexer, RustLexer
from pygments.lexers.make import CMakeLexer
from pygments.lexers.python import PythonLexer

class CustomPythonLexer(PythonLexer):
    """Add distinction between variable and function tokens"""
    name = 'CustomPythonLexer'

    def get_tokens_unprocessed(self, text):
        token_gen = PythonLexer.get_tokens_unprocessed(self, text)
        pending_entry = None
        try:
            while True:
                index, token, value = pending_entry = next(token_gen)
                if token is Name:
                    next_index, next_token, next_value = next(token_gen)
                    if next_value == '(':
                        token = Name.Function
                    yield index, token, value
                    yield next_index, next_token, next_value
                else:
                    yield index, token, value
                pending_entry = None
        except StopIteration:
            if pending_entry is not None:
                yield pending_entry
                pending_entry = None

def setup(app):
    """Replace tabs with 4 spaces"""
    lexers['C++'] = CppLexer()
    lexers['rust'] = RustLexer()
    lexers['CMake'] = CMakeLexer()
    lexers['python'] = CustomPythonLexer()

    ws_filter = VisibleWhitespaceFilter(tabs=' ', tabsize=4)
    for lx in lexers.values():
        lx.add_filter(ws_filter)

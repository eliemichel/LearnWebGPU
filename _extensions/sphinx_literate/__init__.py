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

When the block name starts with "file:", the block is considered as the root
and the remaining of the name is the path of the file into which the tangled
content must be saved, relative to the root tangle directory.

"""

from sphinx.application import Sphinx

from .builder import TangleBuilder
from .directives import setup as setup_directives
from .config import setup as setup_config
from .nodes import setup as setup_nodes
from .handlers import setup as setup_handlers

#############################################################
# Setup

def setup(app: Sphinx):
    setup_config(app)

    setup_nodes(app)

    setup_directives(app)

    setup_handlers(app)

    app.add_builder(TangleBuilder)

    app.add_js_file("sphinx_literate.js")

    return {
        'version': '0.2',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }

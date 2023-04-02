from docutils.nodes import Node

import sphinx
from sphinx.builders import Builder
from sphinx.locale import __
from sphinx.util.osutil import ensuredir

from os import path
from typing import Any, Iterator, Set, Optional

from .registry import CodeBlock, CodeBlockRegistry
from .tangle import tangle

#############################################################
# Builder

class TangleBuilder(Builder):
    name = 'tangle'
    format = 'tangle'
    epilog = __('The tangled source code is in %(outdir)s.')

    def init(self) -> None:
        pass

    def get_outdated_docs(self) -> Iterator[str]:
        for docname in self.env.found_docs:
            if docname not in self.env.all_docs:
                yield docname
                continue
            targetname = path.join(self.outdir, docname + ".meta.txt")
            try:
                targetmtime = path.getmtime(targetname)
            except Exception:
                targetmtime = 0
            try:
                srcmtime = path.getmtime(self.env.doc2path(docname))
                if srcmtime > targetmtime:
                    yield docname
            except OSError:
                # source doesn't exist anymore
                pass

    def get_target_uri(self, docname: str, typ: Optional[str] = None) -> str:
        print(f"get_target_uri(docname={docname}, typ={typ})")
        return ""

    def prepare_writing(self, docnames: Set[str]) -> None:
        print(f"prepare_writing(docnames={docnames})")

    def write_doc(self, docname: str, doctree: Node) -> None:
        print(f"write_doc(docname={docname}, doctree=...)")
        # Get all code blocks whose name start with "file:", these are all the
        # root blocks we tangle.
        lit_codeblocks = CodeBlockRegistry.from_env(self.env)
        for k, lit in lit_codeblocks.items():
            if lit.name.startswith("file:"):
                self.tangle_and_write(lit)

    def tangle_and_write(self, lit: CodeBlock):
        lit_codeblocks = CodeBlockRegistry.from_env(self.env)
        assert(lit.name.startswith("file:"))
        filename = lit.name[len("file:"):].strip()
        if lit.tangle_root is not None:
            filename = path.join(lit.tangle_root, filename)

        tangled_content, root_lit = tangle(
            lit.name,
            lit.tangle_root,
            lit_codeblocks,
            self.app.config,
            lit.source_location.format() + ", "
        )

        outfilename = path.join(self.outdir, filename)
        ensuredir(path.dirname(outfilename))
        try:
            with open(outfilename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(tangled_content))
        except OSError as err:
            logger.warning(__("error writing file %s: %s"), outfilename, err)

    def finish(self) -> None:
        print("finish")

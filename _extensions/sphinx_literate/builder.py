from docutils.nodes import Node

import sphinx
from sphinx.builders import Builder
from sphinx.locale import __
from sphinx.util.osutil import ensuredir
from sphinx.errors import ExtensionError

from os.path import join, dirname, getmtime
from typing import Any, Iterator, Set, Optional
from zipfile import ZipFile
import shutil

from .registry import CodeBlock, CodeBlockRegistry
from .tangle import tangle

#############################################################
# Builder

class TangleBuilder(Builder):
    name = 'tangle'
    format = 'tangle'
    epilog = __('The tangled source code is in %(outdir)s.')

    # Inherited methods

    def init(self) -> None:
        pass

    def get_outdated_docs(self) -> Iterator[str]:
        for docname in self.env.found_docs:
            if docname not in self.env.all_docs:
                yield docname
                continue
            targetname = join(self.outdir, docname + ".meta.txt")
            try:
                targetmtime = getmtime(targetname)
            except Exception:
                targetmtime = 0
            try:
                srcmtime = getmtime(self.env.doc2path(docname))
                if srcmtime > targetmtime:
                    yield docname
            except OSError:
                # source doesn't exist anymore
                pass

    def get_target_uri(self, docname: str, typ: Optional[str] = None) -> str:
        #print(f"get_target_uri(docname={docname}, typ={typ})")
        return ""

    def prepare_writing(self, docnames: Set[str]) -> None:
        #print(f"prepare_writing(docnames={docnames})")
        pass

    def write_doc(self, docname: str, doctree: Node) -> None:
        #print(f"write_doc(docname={docname}, doctree=...)")
        pass

    def finish(self) -> None:
        # Tangle only at the end to account for unordered definitions and inheritance
        registry = CodeBlockRegistry.from_env(self.env)
        for tangle_root in registry.all_tangle_roots():
            self.processed_files = set()

            # Tangle blocks
            for lit in registry.blocks_by_root(tangle_root):
                if lit.name.startswith("file:"):
                    self.tangle_and_write(lit, tangle_root)

            # Fetch extra code
            fetch_files = registry.all_tangle_fetch_files(tangle_root)
            for path, source_location in fetch_files:
                if not path.exists():
                    message = (
                        f"Cannot fetch file {path} for tangle root {tangle_root} " +
                        f"(in lit-setup directive from {source_location.format()})"
                    )
                    raise ExtensionError(message, modname="sphinx_literate")
                self.fetch_file(path, tangle_root)

    # Internal methods

    def tangle_and_write(self, lit: CodeBlock, tangle_root: str | None):
        """
        NB: tangle_root is different from lit.tangle_root in case of inheritance
        """
        registry = CodeBlockRegistry.from_env(self.env)
        assert(lit.name.startswith("file:"))
        filename = lit.name[len("file:"):].strip()
        
        # Easy mistake guard
        if filename in self.processed_files:
            message = (
                f"There are two different blocks with a name 'file: {filename}' that " +
                f"only differ from spaces after 'file:', this is likely a mistake."
            )
            raise ExtensionError(message, modname="sphinx_literate")
        self.processed_files.add(filename)

        if tangle_root is not None:
            filename = join(tangle_root, filename)

        tangled_content, root_lit = tangle(
            lit.name,
            tangle_root,
            registry,
            self.app.config,
            lit.source_location.format() + ", "
        )

        outfilename = join(self.outdir, filename)
        ensuredir(dirname(outfilename))
        try:
            with open(outfilename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(tangled_content))
        except OSError as err:
            logger.warning(__("error writing file %s: %s"), outfilename, err)

    def fetch_file(self, path, tangle_root):
        if path.name.endswith(".zip"):
            with ZipFile(path) as zf:
                zf.extractall(join(self.outdir, tangle_root))
        else:
            shutil.copy(path, join(self.outdir, tangle_root))

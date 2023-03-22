from __future__ import annotations
from typing import Any, Dict, Set
from dataclasses import dataclass, field
from collections import defaultdict

from sphinx.errors import ExtensionError

#############################################################

@dataclass
class SourceLocation:
    """
    Represents a location in the documentation's source
    """

    # Name of the document
    docname: str = ""

    # Line number at which the block was defined in the source document
    lineno: int = -1

    def format(self):
        return f"document '{self.docname}', line {self.lineno}"

#############################################################
# Codeblock

Key = str

@dataclass
class CodeBlock:
    """
    Data store about a code block parsed from a {lit} directive, to be
    assembled when tangling.
    """

    # Name of the code block (see title parsing)
    name: str = ""

    # Source document/line where the block was defined
    source_location: SourceLocation = field(default_factory=SourceLocation)

    # Tangle root as defined by lit-setup at the time the block was created
    tangle_root: str | None = ""

    # A list of lines
    content: List[str] = field(default_factory=list)

    # Target anchor for referencing this code block in internal links
    target: Any = None

    lexer: str | None = None

    # NB: Fields bellow are handled by the registry

    # A block has children when it gets appended/replaced some content in later
    # blocks (this is a basic doubly linked list)
    next: CodeBlock | None = None
    prev: CodeBlock | None = None

    # This is either 'NEW, 'APPEND' or 'REPLACE', telling whether this block's
    # content must be added to the result of evaluating the previous ones or
    # whether it replaces the previous content.
    # The difference between NEW and REPLACE is that REPLACE affects lit
    # references in the parent tangle but NEW creates an independant chain of
    # blocks (which may or may not have the same name as one block from the
    # parent tangle root, but it does not matter).
    relation_to_prev: str = 'NEW'

    # The index of the block in the child list
    child_index: int = 0

    @classmethod
    def build_key(cls, name: str, tangle_root: str | None = None) -> Key:
        if tangle_root is None:
            tangle_root = ""
        return tangle_root + "##" + name

    @property
    def key(self) -> Key:
        return self.build_key(self.name, self.tangle_root)

    def add_block(self, lit: CodeBlock) -> None:
        """
        Add a block at the end of the chained list
        """
        last = self
        while last.next is not None:
            last = last.next
        last.next = lit
        lit.prev = last

        # Update child index for 'lit' and its children
        child_index = last.child_index + 1
        while lit is not None:
            lit.child_index = child_index
            child_index += 1
            lit = lit.next

    def all_content(self):
        """
        Iterate on all lines of content, including children, and overridden
        parent.
        """

        # Find the last REPLACE of the chain
        start = self
        lit = start
        while lit is not None:
            if lit.relation_to_prev == 'REPLACE':
                start = lit
            lit = lit.next

        # If no replace, maybe add source from the parent tangle
        if start.prev is not None and start.relation_to_prev == 'APPEND':
            assert(start.prev.tangle_root != start.tangle_root)
            for l in start.prev.all_content():
                yield l

        # Content of the start and next blocks
        lit = start
        while lit is not None:
            for l in lit.content:
                yield l
            lit = lit.next

    def format(self):
        maybe_root = ''
        if self.tangle_root is not None:
            maybe_root = f" (in root '{self.tangle_root}')"
        return f"'{self.name}'{maybe_root}"

    def link_url(self, fromdocname: str, builder):
        """
        @param fromdocname Name of the document from which the url will be used
        @param builder sphinx html builder (or any object that provides a
                       get_relative_uri method)
        """
        return (
            builder.get_relative_uri(fromdocname, self.source_location.docname)
            + '#' + self.target['refid']
        )

#############################################################

@dataclass
class TangleHierarchyEntry:
    """
    Store options for each tangle root about the first lit-setup directive that
    defiend its parent.
    """
    root: str
    parent: str
    source_location: SourceLocation

#############################################################
# Codeblock registry

class CodeBlockRegistry:
    """
    Holds the various code blocks and prevents duplicates.
    NB: Do not create this yourself, call CodeBlockRegistry.from_env(env)
    """

    @classmethod
    def from_env(cls, env) -> CodeBlockRegistry:
        if not hasattr(env, 'lit_codeblocks'):
            env.lit_codeblocks = CodeBlockRegistry()
        return env.lit_codeblocks

    def __init__(self) -> None:
        # Literate code blocks that have been define, indexed by their key.
        # If blocks with the same key have been appended, they are accessed
        # using the `next` member of CodeBlock.
        self._blocks: Dict[Key,CodeBlock] = {}

        # Store an index of all the references to a block
        # self._references[key] lists all blocks that reference key
        self._references: Dict[Key,Set[Key]] = defaultdict(set)

        # Holds the relationship between different tangle roots.
        # This maps a root to its parent
        self._hierarchy: Dict[str,TangleHierarchyEntry] = {}

    def add_codeblock(self, lit: CodeBlock) -> None:
        """
        Add a new code block to the repository. If a block already exists with
        the same key, an error is raised.
        @param lit block to add
        """
        if "##" in lit.name:
            message = (
                f"The sequence '##' is not allowed in a block name, " +
                f"it is reserved to internal mechanisms.\n"
            )
            raise ExtensionError(message, modname="sphinx_literate")

        key = lit.key
        existing = self.get_by_key(key)

        if existing is not None:
            message = (
                f"Multiple literate code blocks with the same name {lit.format()} were found:\n" +
                f"  - In {existing.source_location.format()}.\n"
                f"  - In {lit.source_location.format()}.\n"
            )
            raise ExtensionError(message, modname="sphinx_literate")

        lit.relation_to_prev = 'NEW'
        self._blocks[key] = lit

    def append_codeblock(self, lit: CodeBlock) -> None:
        """
        Append the content of the code block to the code block that already has
        the same name. Raises an exception if such a block does not exist.
        @param lit block to append
        """
        self._append_or_replace_codeblock(lit, 'APPEND')

    def replace_codeblock(self, lit: CodeBlock) -> None:
        """
        Replace a block and all this children with a new one. Raises an
        exception if such a block does not exist.
        @param lit block to append
        """
        self._append_or_replace_codeblock(lit, 'REPLACE')

    def _append_or_replace_codeblock(self, lit: CodeBlock, relation_to_prev: str):
        """
        Shared behavior between append_codeblock() and replace_codeblock()
        """
        existing = self.get_rec(lit.name, lit.tangle_root)

        if existing is None:
            action_str = {
                'APPEND': "append to",
                'REPLACE': "replace",
            }[relation_to_prev]
            message = (
                f"Trying to {action_str} a non existing literate code blocks {lit.format()}\n" +
                f"  - In {lit.source_location.format()}.\n"
            )
            raise ExtensionError(message, modname="sphinx_literate")

        lit.relation_to_prev = relation_to_prev
        
        if existing.tangle_root != lit.tangle_root:
            self._blocks[lit.key] = lit
            lit.prev = existing
        else:
            existing.add_block(lit)

    def add_reference(self, referencer: Key, referencee: Key) -> None:
        """
        Signal that `referencer` contains a reference to `referencee`
        """
        self._references[referencee].add(referencer)

    def merge(self, other: CodeBlockRegistry) -> None:
        """
        Merge antoher registry into this one.
        """
        for lit in other.blocks():
            self.add_codeblock(lit, refs)
        for key, refs in other._references.items():
            self._references[key].update(refs)

    def remove_codeblocks_by_docname(self, docname: str) -> None:
        # TODO: when supporting cross-document REPLACE, be careful here
        self._blocks = {
            key: lit
            for key, lit in self._blocks.items()
            if lit.source_location.docname != docname
        }

    def set_tangle_parent(self, tangle_root: str, parent: str, source_location: SourceLocation) -> None:
        """
        Set the parent for a given tangle root. Fail if a different root has
        already been defined.
        @param tangle_root name of the tangle root for which we define a parent
        @param parent name of the tangle to set as parent
        @param docname Name of the document that sets this parenting
        @param lineno Line where the lit-config that sets this is defined
        """
        existing = self._hierarchy.get(tangle_root)
        if existing is not None:
            if existing.parent != parent:
                message = (
                    f"Attempting to set the tangle parent for root '{tangle_root}' to a different value:\n" +
                    f"  Was set to '{existing.parent}' in {existing.source_location.format()}.\n"
                    f"  But trying to set to '{parent}' in {source_location.format()}.\n"
                )
                raise ExtensionError(message, modname="sphinx_literate")
        else:
            self._hierarchy[tangle_root] = TangleHierarchyEntry(
                root = tangle_root,
                parent = parent,
                source_location = source_location,
            )

    def blocks(self) -> CodeBlock:
        return self._blocks.values()

    def get(self, name: str, tangle_root: str | None = None) -> CodeBlock:
        return self.get_by_key(CodeBlock.build_key(name, tangle_root))

    def get_rec(self, name: str, tangle_root: str | None, override_tangle_root: str | None = None) -> CodeBlock:
        """
        Get a block and recursively search for it in parent tangles
        If a root override is provided, first look there for a block that has
        a 'REPLACE' or 'APPEND' relation.
        """

        # Explore downstream parent tree towards the 'override' root.
        # From this chain of blocks, we keep the one that is just before the
        # first 'NEW' (beyond chich blocks with the same names are not
        # overrides, they are unrelated).
        found = None
        tr = override_tangle_root
        while tr is not None and tr != tangle_root:
            lit = self.get(name, tr)
            if lit is not None:
                if lit.relation_to_prev == 'NEW':
                    found = None # reset
                elif found is None:
                    found = lit
            tr = self._parent_tangle_root(tr)

        if found is not None:
            return found

        # In upstream tangle tree, return the first match
        prev_tr = ()
        tr = tangle_root
        while tr != prev_tr:
            found = self.get(name, tr)
            if found is not None:
                return found
            prev_tr = tr
            tr = self._parent_tangle_root(tr)
        return None

    def get_by_key(self, key: Key) -> CodeBlock:
        return self._blocks.get(key)

    def get_rec_by_key(self, key: Key) -> CodeBlock:
        tangle_root, name = key.split("##")
        return self.get_rec(name, tangle_root)

    def keys(self) -> dict_keys:
        return self._blocks.keys()

    def items(self) -> dict_items:
        return self._blocks.items()

    def references_to_key(self, key: Key) -> List[Key]:
        return list(self._references[key])

    def _parent_tangle_root(self, tangle_root: str) -> str | None:
        h = self._hierarchy.get(tangle_root)
        return h.parent if h is not None else None

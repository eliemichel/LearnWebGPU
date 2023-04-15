from __future__ import annotations
from typing import Any, Dict, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
from pathlib import Path
import random

from sphinx.errors import ExtensionError

#############################################################

BlockOptions = Set[str|Tuple[str]]

Key = str

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

@dataclass
class InsertLocation:
    # Either 'BEFORE' or 'AFTER'
    placement: str

    # Substring used to detect the line before/after which inserting
    pattern: str

#############################################################
# Codeblock

@dataclass
class CodeBlock:
    """
    Data store about a code block parsed from a {lit} directive, to be
    assembled when tangling.
    TODO This class should be split in 2 parts:
     1. What directly comes from a given source block
     2. What relates to CodeBlock being a nodes in the block graph
    """

    # Name of the code block (see title parsing)
    name: str = ""

    # Source document/line where the block was defined
    source_location: SourceLocation = field(default_factory=SourceLocation)

    # Tangle root as defined by lit-setup at the time the block was created
    tangle_root: str | None = None

    # A list of lines
    content: List[str] = field(default_factory=list)

    # Target anchor for referencing this code block in internal links
    target: Any = None

    lexer: str | None = None

    # NB: Fields bellow are handled by the registry

    # Unique identifier, used for recovery after deserializing (which Sphinx
    # does when pickling)
    uid: str | None = None

    # A block has children when it gets appended/replaced some content in later
    # blocks (this is a basic doubly linked list)
    next: CodeBlock | None = None
    prev: CodeBlock | None = None

    # This is either 'NEW*'', 'APPEND', 'PREPEND' or 'REPLACE', telling whether
    # this block's content must be added to the result of evaluating the
    # previous ones or whether it replaces the previous content.
    # The difference between NEW and REPLACE is that REPLACE affects lit
    # references in the parent tangle but NEW creates an independant chain of
    # blocks (which may or may not have the same name as one block from the
    # parent tangle root, but it does not matter).
    # The special value 'INSERT' means that instead of considering the content
    # of this block, we fetch from another one and insert before or after a
    # given line.
    # The value 'INSERTED' means a new block that is inserted somewhere, whereas
    # INSERT is the value used for the modifier node in the chain of the target
    # of the insertion.
    relation_to_prev: str = 'NEW'

    # When relation_to_prev is 'INSERT', the content of this block is inserted
    inserted_block: CodeBlock | None = None

    # When relation_to_prev is 'INSERT', the inserted content is placed here
    inserted_location: InsertLocation | None = None

    # The index of the block in the child list
    child_index: int = 0

    # Hide by default in HTML
    hidden: bool = False

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

    def all_content(self, registry: CodeBlockRegistry, tangle_root: str | None = None):
        """
        Iterate on all lines of content, including children, and overridden
        parent.
        @param registry must be provided to resolve inserted blocks correctly.
        @param tangle_root is the root from which this content is evaluated.
                           It may differs from the block's tangle in case of
                           inheritance and the content of the block is
                           different if referencing inserted blocks that are
                           redefined in children.
        """
        if tangle_root is None:
            tangle_root = self.tangle_root

        # Find the last REPLACE of the chain
        start = self
        lit = start
        while lit is not None:
            if lit.relation_to_prev == 'REPLACE':
                start = lit
            lit = lit.next

        # Consolidate all INSERT nodes downstream of the last REPLACE
        # Then create the maybeInsert function to handle them
        insert_nodes = {
            'BEFORE': defaultdict(list), # pattern: nodes
            'AFTER': defaultdict(list), # pattern: nodes
        }
        lit = start
        while lit is not None:
            if lit.relation_to_prev == 'INSERT':
                assert(not lit.content)
                loc = lit.inserted_location
                insert_nodes[loc.placement][loc.pattern].append(lit)
            lit = lit.next

        def _maybeInsertAux(l, placement):
            matched = []
            for pattern, nodes in insert_nodes[placement].items():
                if pattern in l:
                    for n in nodes:
                        inserted_block = n.inserted_block
                        if registry is not None:
                            inserted_block = registry.get_rec_by_key(n.inserted_block.key, override_tangle_root=tangle_root)
                        for ll in inserted_block.all_content(registry, tangle_root):
                            yield ll
                    matched.append(pattern)
            for pattern in matched:
                del insert_nodes[placement][pattern]

        def maybeInsert(l):
            for ll in _maybeInsertAux(l, 'BEFORE'):
                yield ll
            yield l
            for ll in _maybeInsertAux(l, 'AFTER'):
                yield ll

        # If no replace, maybe add source from the parent tangle
        if start.prev is not None and start.relation_to_prev in {'APPEND', 'INSERT'}:
            assert(start.prev.tangle_root != start.tangle_root)
            for l in start.prev.all_content(registry, tangle_root):
                for ll in maybeInsert(l):
                    yield ll

        # Content of the start and next blocks
        lit = start
        # (Because of PREPEND we can no longer "stream" the yields, we need to
        # save everything in a list and yields lines afterwards.)
        consolidated_content = []
        test = False
        while lit is not None:
            chunk = []
            for l in lit.content:
                for ll in maybeInsert(l):
                    chunk.append(ll)
            if lit.relation_to_prev == 'PREPEND':
                consolidated_content.insert(0, chunk)
            else:
                consolidated_content.append(chunk)
            lit = lit.next

        for chunk in consolidated_content:
            for ll in chunk:
                yield ll

        # Add parent tangle afterwards if this block is prepended
        if start.prev is not None and start.relation_to_prev in {'PREPEND'}:
            assert(start.prev.tangle_root != start.tangle_root)
            for l in start.prev.all_content(registry, tangle_root):
                for ll in maybeInsert(l):
                    yield ll

        for placement, node_dict in insert_nodes.items():
            for pattern, nodes in node_dict.items():
                for n in nodes:
                    message = (
                        f"The block {n.inserted_block.format()} was supposed to be inserted {placement.lower()} "
                        + f"\"{pattern}\" in block {self.format()}, "
                        + f"but no occurrence of this text was found."
                    )
                    raise ExtensionError(message, modname="sphinx_literate")

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

    # Where the parenting relation was defined
    source_location: SourceLocation

    # Files copied to the tangle root
    fetch_files: List[Path]

#############################################################

@dataclass
class MissingCodeBlock:
    """
    We allow missing blocks to enable parallel compilation. Missing
    blocks are resolved when combining multiple registers comming from
    parallel units.
    """
    # The key of the referee, that expected its 'prev' to exist
    key: Key
    # The relation of the referee to the expected block
    relation_to_prev: str

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

        # We allow missing blocks to enable parallel compilation. Missing
        # blocks are resolved when combining multiple registers comming from
        # parallel units.
        self._missing: List[MissingCodeBlock] = []

    @classmethod
    def create_uid(cls):
        return ''.join([random.choice('123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ') for _ in range(16)])

    def register_codeblock(self, lit: CodeBlock, options: BlockOptions = set()) -> None:
        """
        Add a new code block to the repository. The behavior depends on the
        options:
         - If 'APPEND' is present in the options, append the content of the
           code block to the code block that already has the same name.
           If such a block does not exist, it is added to the list of missing
           blocks (so check_integrity() will raise an exception).
         - If 'PREPEND' is present in the options, add the content of the code
           block to beginning of the code block that already has the same name.
           If such a block does not exist, it is added to the list of missing
           blocks (so check_integrity() will raise an exception).
         - If 'REPLACE' is in the options, replace a block and all its children
           with a new one. If such a block does not exist, it is added to the
           list of missing blocks.
         - Otherwise, the block is added as NEW and if a block already exists
           with the same key, an error is raised.
        @param lit block to register
        @param options the options
        """
        assert(lit.uid is None)
        lit.uid = self.create_uid()

        opt_dict = {
            (x[0] if type(x) == tuple else x): x
            for x in options
        }
        lit.hidden = 'HIDDEN' in options
        if 'APPEND' in options:
            self._override_codeblock(lit, 'APPEND')
        elif 'PREPEND' in options:
            self._override_codeblock(lit, 'PREPEND')
        elif 'REPLACE' in options:
            self._override_codeblock(lit, 'REPLACE')
        elif 'INSERT' in opt_dict:
            # In this case we add the block as new, and add a "modifier" block
            # to the chain of the target of the insertion to notify it that it
            # must fetch data from this new block chain.
            self._add_codeblock(lit)

            _, block_name, placement, pattern = opt_dict['INSERT']
            modifier = CodeBlock(
                name = block_name,
                tangle_root = lit.tangle_root,
                source_location = lit.source_location,
                target = lit.target,
            )
            modifier.inserted_location = InsertLocation(placement, pattern)
            modifier.inserted_block = lit
            self._override_codeblock(modifier, 'INSERT')
            assert(modifier.prev is not None or self._missing[-1].key == modifier.key)

            lit.relation_to_prev = 'INSERTED'
            lit.prev = modifier
        else:
            lit.relation_to_prev = 'NEW'
            self._add_codeblock(lit)

        self._fix_missing_referees(lit)

    def _fix_missing_referees(self, lit):
        """
        Notify all children tangles that a new block `lit` is defined and thus
        may no longer be missing.
        Also set child_lit.prev
        FIXME: This is inefficient, maybe we should manage missings
        differently (e.g., by not storing them and only testing once the full
        register is created.)
        """
        for child_tangle in self._all_children_tangle_roots(lit.tangle_root):
            new_missing_list = []
            for missing in self._missing:
                if missing.key == CodeBlock.build_key(lit.name, child_tangle):
                    child_lit = self.get_by_key(missing.key)
                    assert(child_lit.prev is None)
                    assert(child_lit.relation_to_prev not in {'NEW', 'INSERTED'})
                    child_lit.prev = lit
                else:
                    new_missing_list.append(missing)
            self._missing = new_missing_list

    def _add_codeblock(self, lit: CodeBlock) -> None:
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

        self._blocks[key] = lit

    def _override_codeblock(self, lit: CodeBlock, relation_to_prev: str):
        """
        Shared behavior between append_codeblock() and replace_codeblock()
        @param args extra arguments precising the relation to previous block
        """
        lit.relation_to_prev = relation_to_prev

        existing = self.get_rec(lit.name, lit.tangle_root)
        
        if existing is None:
            self._missing.append(
                MissingCodeBlock(lit.key, lit.relation_to_prev)
            )
            # Add to the list of block with no parent, even though the
            # relation_to_prev is not NEW. This will be addressed when
            # resolving missings.
            self._blocks[lit.key] = lit
            lit.prev = None
        elif existing.tangle_root != lit.tangle_root:
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
        Merge antoher registry into this one. This one comes from a document
        defined before the other one (matters when resolving missing blocks).
        The other registry must no longer be used after this.
        """
        X = next(iter(other._blocks.values()))
        # Merge tangle hierarchies
        for h in other._hierarchy.values():
            self.set_tangle_parent(h.root, h.parent, h.source_location, h.fetch_files)

        # Merge blocks
        for lit in other.blocks():
            if lit.relation_to_prev in {'NEW', 'INSERTED'}:
                self._add_codeblock(lit)
            else:
                self._override_codeblock(lit, lit.relation_to_prev)
            self._fix_missing_referees(lit)
            self.check_integrity(allow_missing=True)

        # Merge cross-references
        for key, refs in other._references.items():
            self._references[key].update(refs)

    def remove_codeblocks_by_docname(self, docname: str) -> None:
        # TODO: when supporting cross-document REPLACE, be careful here
        self._blocks = {
            key: lit
            for key, lit in self._blocks.items()
            if lit.source_location.docname != docname
        }

    def set_tangle_parent(self, tangle_root: str, parent: str, source_location: SourceLocation = SourceLocation(), fetch_files: List[Path] = []) -> None:
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
            existing.fetch_files += fetch_files
        elif tangle_root == parent:
            message = (
                f"A tangle root cannot be its own parent! \n" +
                f"  For tangle root '{tangle_root}' in {source_location.format()}.\n"
            )
            raise ExtensionError(message, modname="sphinx_literate")
        else:
            self._hierarchy[tangle_root] = TangleHierarchyEntry(
                root = tangle_root,
                parent = parent,
                source_location = source_location,
                fetch_files = fetch_files,
            )

            # Now that 'tangle_root' has a parent, blocks that were missing for
            # this tangle may be resolved
            def isStillUnresolved(missing):
                missing_tangle_root, missing_name = missing.key.split("##")
                if missing_tangle_root == tangle_root:
                    child_lit = self.get_by_key(missing.key)
                    if child_lit is not None:
                        assert(child_lit.prev is None)
                        assert(child_lit.relation_to_prev not in {'NEW', 'INSERTED'})
                        child_lit.prev = self.get_rec(child_lit.name, parent)
                        assert(child_lit.prev is not None)
                        assert(child_lit.prev.tangle_root != child_lit.tangle_root)
                        return False
                return True
            self._missing = list(filter(isStillUnresolved, self._missing))

    def blocks(self) -> List[CodeBlock]:
        return self._blocks.values()

    def blocks_by_root(self, tangle_root: str | None) -> List[CodeBlock]:
        """
        If a tangle root is given, return only blocks for this tangle root,
        including the inherited ones
        """
        block_names = set()
        for b in self._blocks.values():
            if self.get_rec(b.name, tangle_root) is not None:
                block_names.add(b.name)
        return [
            self.get_rec(name, tangle_root)
            for name in block_names
        ]

    def get(self, name: str, tangle_root: str | None = None) -> CodeBlock:
        return self.get_by_key(CodeBlock.build_key(name, tangle_root))

    def get_rec(self, name: str, tangle_root: str | None, override_tangle_root: str | None = None) -> CodeBlock:
        """
        Get a block and recursively search for it in parent tangles
        If a root override is provided, first look there for a block that has
        a 'APPEND', 'PREPEND' or 'REPLACE' relation.
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

        if tangle_root is None:
            return self.get(name)

        # In upstream tangle tree, return the first match
        tr = tangle_root
        while tr is not None:
            found = self.get(name, tr)
            if found is not None:
                return found
            tr = self._parent_tangle_root(tr)
        return None

    def get_by_key(self, key: Key) -> CodeBlock:
        return self._blocks.get(key)

    def get_rec_by_key(self, key: Key, override_tangle_root: str | None = None) -> CodeBlock:
        tangle_root, name = key.split("##")
        return self.get_rec(name, tangle_root, override_tangle_root)

    def get_by_uid(self, uid: str) -> CodeBlock | None:
        for b in self._blocks.values():
            bb = b
            while bb is not None:
                if bb.uid == uid:
                    return bb
                bb = bb.next

    def keys(self) -> dict_keys:
        return self._blocks.keys()

    def items(self) -> dict_items:
        return self._blocks.items()

    def references_to_key(self, key: Key) -> List[Key]:
        return list(self._references[key])

    def all_tangle_roots(self) -> List[str|None]:
        ret = set()
        ret.update({
            b.tangle_root
            for b in self._blocks.values()
        })
        ret.update({
            h.root
            for h in self._hierarchy.values()
        })
        ret.update({
            h.parent
            for h in self._hierarchy.values()
        })
        return list(ret)

    def get_tangle_info(self, tangle_root: str) -> TangleHierarchyEntry:
        return self._hierarchy.get(tangle_root)

    def all_tangle_fetch_files(self, tangle_root) -> List[(Path, SourceLocation)]:
        fetch_files = []
        h = self._hierarchy.get(tangle_root)
        while h is not None:
            fetch_files += [
                (f, h.source_location)
                for f in h.fetch_files
            ]
            h = self._hierarchy.get(h.parent)
        h = self._hierarchy.get(tangle_root)
        return fetch_files

    def _parent_tangle_root(self, tangle_root: str) -> str | None:
        h = self._hierarchy.get(tangle_root)
        return h.parent if h is not None else None

    def _children_tangle_roots(self, tangle_root: str) -> List[str] | None:
        """Return direct children"""
        return [
            h.root
            for h in self._hierarchy.values()
            if h.parent == tangle_root
        ]

    def _all_children_tangle_roots(self, tangle_root: str) -> List[str] | None:
        """Recursively return all children"""
        children = set(self._children_tangle_roots(tangle_root))
        prev_len_children = -1
        while len(children) != prev_len_children:
            prev_len_children = len(children)
            for child in list(children):  # iterate on a copy
                children.update(
                    self._children_tangle_roots(child)
                )
        return list(children)

    def check_integrity(self, allow_missing=False):
        """
        Thi is called when the whole doctree has been seen, it checks that
        there is no more missing block otherwise throws an exception.
        """
        missing_by_key = {
            missing.key: missing
            for missing in self._missing
        }
        for b in self._blocks.values():
            bb = b
            while bb is not None:
                if bb.prev is None and bb.relation_to_prev != 'NEW':
                    assert(bb.key in missing_by_key)
                    assert(missing_by_key[bb.key].relation_to_prev == bb.relation_to_prev)
                bb = bb.next

        if allow_missing:
            return

        for missing in self._missing:
            lit = self.get_by_key(missing.key)

            # Sanity checks
            assert(lit is not None)
            missing_root, missing_name = missing.key.split("##", 1)
            missing_root_parent = self._parent_tangle_root(missing_root)
            if missing_root_parent is not None:
                #assert(self.get_rec(missing_name, missing_root_parent) is None)
                # Accept that this may be wrong, this whole _missing thing is overengineered anyways
                if self.get_rec(missing_name, missing_root_parent) is not None:
                    break

            action_str = {
                'APPEND': "append to",
                'PREPEND': "prepend to",
                'REPLACE': "replace",
                'INSERT': "insert to",
                'INSERTED': "???",
            }[missing.relation_to_prev]
            message = (
                f"Trying to {action_str} a non existing literate code blocks {lit.format()}\n" +
                f"  - In {lit.source_location.format()}.\n"
            )
            raise ExtensionError(message, modname="sphinx_literate")

    def pretty_dump(self, options: List[str] = set()):
        """
        Display debug information about the registry.
        Used by {lit-registry} directive.
        """
        options = set()
        ret = []
        ret += ["== Registry dump =="]
        ret += ["Blocks:"]
        for lit in self._blocks.values():
            ret += [
                f" - {lit.name}"
                + (f" ({lit.tangle_root})" if lit.tangle_root is not None else "")
                + f" [{lit.relation_to_prev}]"
            ]
            if 'SHOW LOCATION' in options:
                ret += [f"   | From: " + lit.source_location.format()]

            if lit.prev is not None:
                ret += ["   | Prev: " + lit.prev.name + (f" ({lit.prev.tangle_root})" if lit.prev.tangle_root is not None else "")]

            next_lit = lit.next
            while next_lit is not None:
                ret += [
                    "   | Next: " + next_lit.name
                    + (f" ({next_lit.tangle_root})" if next_lit.tangle_root is not None else "")
                    + f" [{next_lit.relation_to_prev}]"
                ]
                next_lit = next_lit.next
        ret += [""]
        ret += ["Hierarchy:"]
        for h in self._hierarchy.values():
            ret += [f" - {h.root}"]
            ret += [f"   | Parent: {h.parent} [exists: {h.parent in self._hierarchy}]"]
            if 'SHOW LOCATION' in options:
                ret += [f"   | From: " + h.source_location.format()]
            ret += [f"   | Fetch files: {h.fetch_files}"]
        ret += [""]
        ret += ["Missing:"]
        for missing in self._missing:
            ret += [f" - {missing.key} [{missing.relation_to_prev}]"]
        return ret

from typing import List

from .registry import CodeBlock, CodeBlockRegistry
from .parse import parse_block_link

from sphinx.errors import ExtensionError

#############################################################
# Private

def _tangle_rec(
    lit: CodeBlock,
    registry: CodeBlockRegistry,
    override_tangle_root: str,
    begin_ref: str, # config
    end_ref: str, # config
    tangled_content, # return list
    prefix = "" # for recursive use only
) -> None:
    assert(lit is not None)
    for line in lit.all_content(registry, override_tangle_root):
        # TODO: use parse.parse_block_content here?
        subprefix = None
        link = None
        begin_offset = line.find(begin_ref)
        if begin_offset != -1:
            end_offset = line.find(end_ref, begin_offset)
            if end_offset != -1:
                subprefix = line[:begin_offset]
                link = line[begin_offset+len(begin_ref):end_offset]
        if link is not None:
            parsed_link = parse_block_link(link, lit.tangle_root)
            sublit = registry.get_rec_by_key(parsed_link.key, override_tangle_root=override_tangle_root)
            if sublit is None:
                message = (
                    f"Literate code block not found: '{parsed_link.key}' " +
                    f"(in lit directive from {lit.source_location.format()}, " +
                    f"tangle root {lit.tangle_root})"
                )
                raise ExtensionError(message, modname="sphinx_literate")
            _tangle_rec(
                sublit,
                registry,
                override_tangle_root,
                begin_ref,
                end_ref,
                tangled_content,
                prefix=prefix + subprefix
            )
        else:
            tangled_content.append(prefix + line)

#############################################################
# Public

def tangle(
    block_name: str,
    tangle_root: str | None,
    registry: CodeBlockRegistry,
    config, # sphinx app config
    error_context: str = ""
) -> List[str]:
    """
    Tangle a given code block, i.e. resolve all the references to generate a
    full code without any more pending reference in it.
    @param block_name the name of the block to tangle
    @param tangle_root the name of the root directory: two code blocks with the
           same name may exist only if they belong to different root directories.
    @param registry the registry containing all the code blocks extracted
                    from the source documentation.
    @param config sphinx app config
    @param error_context optional string added to error messages
    @return the generated source code as a list of lines, and the root lit block
    """
    lit = registry.get_rec(block_name, tangle_root)
    if lit is None:
        message = (
            f"Literate code block not found: '{block_name}' " +
            f"({error_context}in root '{tangle_root}')"
        )
        raise ExtensionError(message, modname="sphinx_literate")

    tangled_content = []
    _tangle_rec(
        lit,
        registry,
        tangle_root,
        config.lit_begin_ref,
        config.lit_end_ref,
        tangled_content,
    )
    return tangled_content, lit

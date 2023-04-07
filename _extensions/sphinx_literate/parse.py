from typing import List, Dict, Set, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import random
import re

from .registry import CodeBlock, Key, BlockOptions

from sphinx.errors import ExtensionError

#############################################################
# Block Title

@dataclass
class ParsedBlockTitle:
    """
    The raw title of a lit block looks like:

        {lit} Language, The title (some options)

    The title must not contain comma nor parenthesis.
    The language and options are optional.

    Note that we do not used Sphinx default mechanism for options in order to
    keep it more literate (closer to what a human would spontaneously write).
    """

    # Name of the block, used to reference it
    name: str = ""

    # Name of the language lexer
    lexer: str | None = None

    # Possible options are 'APPEND', 'REPLACE', ('INSERT AFTER', "foo", "bar"), ...
    options: BlockOptions = field(default_factory=set)

#############################################################

def parse_option(raw_option: str) -> str|Tuple[str]:
    # TODO: route config up to here
    begin_ref = '{{' # config.lit_begin_ref
    end_ref = '}}' # config.lit_end_ref

    raw_option = raw_option.strip()
    if raw_option.lower().startswith("insert in " + begin_ref.lower()):
        offset = len("insert in " + begin_ref)
        i = raw_option.find(end_ref, offset)
        if i == -1:
            raise ExtensionError(f"Unable to parse option '{raw_option}' (could not find end of block name)")
        block_name = raw_option[offset:i]
        j = raw_option.find('"', i)
        placement = raw_option[i+len(end_ref):j].strip().upper()
        if j == -1:
            raise ExtensionError(f"Unable to parse option '{raw_option}' (could not find beginning of line pattern)")
        if raw_option[-1] != '"':
            raise ExtensionError(f"Unable to parse option '{raw_option}' (should end with '\"')")
        pattern = raw_option[j+1:-1]
        return ('INSERT', block_name, placement, pattern)
        return ('INSERT BEFORE', block_name, pattern)
    else:
        return raw_option.upper()

def parse_block_title_options(raw_options: str) -> Set[str|Tuple[str]]:
    if raw_options is None:
        return set()
    raw_options = raw_options[1:-1]

    # Parsing automata, possible states:
    (
        DEFAULT,
        IN_STRING,
        IN_STRING_ESCAPE,
    ) = range(3)
    # Possible actions:
    (
        ACCUMULATE,
        NEW_TOKEN,
        IGNORE,
    ) = range(3)
    transitions = {
        DEFAULT: {
            '"': (IN_STRING, ACCUMULATE),
            ',': (DEFAULT, NEW_TOKEN),
            ...: (DEFAULT, ACCUMULATE),
        },
        IN_STRING: {
            '\\': (IN_STRING_ESCAPE, IGNORE),
            '"': (DEFAULT, ACCUMULATE),
            ...: (IN_STRING, ACCUMULATE),
        },
        IN_STRING_ESCAPE: {
            ...: (IN_STRING, ACCUMULATE),
        },
    }
    cursor = 0
    state = DEFAULT
    token = ""
    all_tokens = []
    while cursor < len(raw_options):
        char = raw_options[cursor]
        cursor += 1
        tr = transitions[state]
        state, action = tr.get(char, tr[...])
        if action == NEW_TOKEN:
            all_tokens.append(token)
            token = ""
        elif action == ACCUMULATE:
            token += char
        elif action == IGNORE:
            pass
    all_tokens.append(token)

    return {
        parse_option(opt)
        for opt in all_tokens
    }

def parse_block_title(raw_title: str) -> ParsedBlockTitle:
    """
    This parse a literate code block title (@see ParsedBlockTitle)
    @param raw_title title as returned by Directive.arguments[0]
    @return a parsed title object
    """
    m = re.match(r"^((?P<lexer>[^(,]*),)?(?P<name>[^(,]*)(?P<options>\(.*\))?$", raw_title.strip())

    if m is None:
        message = (
            f"Invalid block name: '{raw_title}'" +
            "note: At most 1 comma is allowed, to specify the language, but the name cannot contain a comma."
        )
        raise ExtensionError(message, modname="sphinx_literate")

    name = m.group("name").strip()

    lexer = m.group("lexer")
    if lexer is not None:
        lexer = lexer.strip()

    options = parse_block_title_options(m.group("options"))

    return ParsedBlockTitle(
        name = name,
        lexer = lexer,
        options = options,
    )

#############################################################
# Block Content

Uid = str

@dataclass
class BlockLink:
    """
    Link to a literate block
    """

    # Name of the referenced block
    key: Key = ""

    # Possible options are 'HIDDEN'
    options: Set[str] = field(default_factory=list)

@dataclass
class ParsedBlockContent:
    """
    The content of each literate block is parsed and references are replaced
    with unique ids (hashcode) so that they can be recognized after syntax
    highlight is added.
    """

    # Content of the block where references are replaced with uids
    content: List[str]

    # Holds the mapping from the uids and the original references to other
    # literate code blocks.
    uid_to_block_link: Dict[Uid,BlockLink]

#############################################################

def generate_uid() -> Uid:
    return "_" + "".join([random.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for _ in range(32)])

#############################################################

def parse_block_link(content: str, tangle_root: str | None) -> BlockLink:
    m = re.match(r"(?P<name>[^(,]*)(?P<options>\(.*\))?", content)

    if m is None:
        message = f"Invalid block link: '{content}'"
        raise ExtensionError(message, modname="sphinx_literate")

    name = m.group("name").strip()

    options = m.group("options")
    if options is None:
        options = set()
    else:
        options = {
            opt.strip().upper()
            for opt in options[1:-1].split(',')
        }

    return BlockLink(
        key = CodeBlock.build_key(name, tangle_root),
        options = options,
    )

def parse_block_content(content: List[str], tangle_root: str | None, config) -> ParsedBlockContent:
    """
    This reads the raw source code and extracts {{references}} to other blocks,
    not to disturb the syntax highlighter.

    @note At this stage we do not check whether block names exist.

    @param content original source code with literate references
    @param tangle_root context of the block
    @param config sphinx config
    @return a parsed block object
    """
    parsed = ParsedBlockContent(
        content = [],
        uid_to_block_link = {},
    )

    raw_source = '\n'.join(content)

    begin_ref = config.lit_begin_ref
    end_ref = config.lit_end_ref

    offset = 0
    parsed_source = ""
    while True:
        begin_offset = raw_source.find(begin_ref, offset)
        if begin_offset == -1:
            break
        end_offset = raw_source.find(end_ref, begin_offset)
        if end_offset == -1:
            print(f"Warning: Found a reference openning '{begin_ref}' but reached end of block before finding the reference closing '{end_ref}'")
            break
        uid = generate_uid()
        block_name = raw_source[begin_offset+len(begin_ref):end_offset]
        parsed.uid_to_block_link[uid] = parse_block_link(block_name, tangle_root)
        parsed_source += raw_source[offset:begin_offset]
        parsed_source += uid
        offset = end_offset + len(end_ref)

    parsed_source += raw_source[offset:]

    parsed.content = parsed_source.split('\n')

    return parsed

#############################################################

def parse_fetched_files(raw_file_list: str | None, docpath: str) -> List[Path]:
    if raw_file_list is None:
        return []
    return [
        Path(docpath).parent.joinpath(f).resolve()
        for f in raw_file_list.split(",")
    ]

#############################################################

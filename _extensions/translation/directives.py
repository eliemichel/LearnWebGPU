from typing import List

from docutils import nodes
from docutils.nodes import Node, Element
from sphinx.application import Sphinx
from docutils.statemachine import StringList

from sphinx.util.docutils import SphinxDirective

import subprocess
import time

#############################################################

def git(*args):
    return subprocess.run(["git", *args], capture_output=True).stdout.decode()

#############################################################

def getLastChange(filepath):
    info = git("log", "-1", '--pretty=%h;%ct', filepath)
    if not info:
        return "", int(time.time())
    else:
        hash, timestamp = info.split(";")
        return hash, int(timestamp)

#############################################################

class TranslationWarningDirective(SphinxDirective):
    """
    A warning that is displayed only when a page is older than the one it is
    supposed to be a translation of.
    """

    has_content = True
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True

    def run(self) -> List[Node]:
        self.assert_has_content()

        title, original_file_relative = [ x.strip() for x in self.arguments[0].split(",") ]
        
        _, original_file = self.env.relfn2path(original_file_relative, self.env.docname)
        _, translated_file = self.env.relfn2path(self.env.docname, self.env.docname)
        original_url = original_file_relative
        contribute_url = f"https://github.com/eliemichel/LearnWebGPU/edit/main/{self.env.docname}.md"

        original_hash, original_timestamp = getLastChange(original_file)
        _, translated_timestamp = getLastChange(translated_file)
        
        if translated_timestamp > original_timestamp:
            return [] # Nothing to display

        diff = git("diff", original_hash, "HEAD", "--", original_file)

        diff_block = f"`````{{admonition}} Diff\n:class: diff\n````diff\n{diff}\n````\n`````"

        container = nodes.container()
        block_text = f"``````{{admonition}} {title}\n{self.block_text}\n{diff_block}\n``````"
        block_text = block_text.replace("%original%", original_url)
        block_text = block_text.replace("%contribute%", contribute_url)
        source = StringList(block_text.splitlines())
        self.state.nested_parse(source, 0, container)
        return [container]

#############################################################

def setup(app: Sphinx) -> None:
    app.add_directive("translation-warning", TranslationWarningDirective)

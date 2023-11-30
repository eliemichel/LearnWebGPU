import contextlib
import os
import re
from typing import TYPE_CHECKING

from sphinx.project import Project
from sphinx.util.osutil import path_stabilize, relpath

from collections.abc import Iterable

#############################################################

class TranslatedProject(Project):
    def __init__(self, srcdir: str | os.PathLike[str], source_suffix: Iterable[str]) -> None:
        super().__init__(srcdir, source_suffix)

        # Only the first matching rule is applied, there is no possible cascade
        self.rewriting_rules = [
            # matched pattern, replacement string (using \1 for the 1-st match group, etc.)
            (r"^translation/", "")
        ]

    def path2doc(self, filename: str | os.PathLike[str]) -> str | None:
        """Return the docname for the filename if the file is a document.

        *filename* should be absolute or relative to the source directory.
        """
        docname = super().path2doc(filename)
        
        if docname is None:
            return None

        # Rewriting
        for pattern, replacement in self.rewriting_rules:
            if re.match(pattern, docname):
                docname = re.sub(pattern, replacement, docname)
                break

        return docname

#############################################################
# Setup

def setup(app):
    app.project_class = TranslatedProject

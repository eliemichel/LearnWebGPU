from typing import List

from docutils import nodes
from docutils.nodes import Node, Element
from docutils.statemachine import StringList
from docutils.parsers.rst.directives.images import Figure

from sphinx.util.docutils import SphinxDirective
from sphinx.application import Sphinx

from copy import deepcopy

#############################################################

def findNodeWithType(target_type, node_list):
    for n in node_list:
        if isinstance(n, target_type):
            return n

#############################################################

class ThemedFigureDirective(Figure):
    """
    A figure that switches depending on the dark/light theme
    """

    def run(self) -> List[Node]:
        url_template = self.arguments[0]
        self.arguments[0] = url_template.replace("{theme}", "light")
        
        node_list = super().run()

        figure_node = findNodeWithType(nodes.figure, node_list)
        if not figure_node:
            print(node_list)
            raise Exception("Could not find generated figure in themed-figure")

        light_image_node = findNodeWithType(nodes.image, figure_node)
        if not light_image_node:
            print(figure_node)
            raise Exception("Could not find generated image in themed-figure")

        # Create dark copy
        dark_image_node = deepcopy(light_image_node)
        dark_image_node['uri'] = url_template.replace("{theme}", "dark")

        # Add class
        light_image_node['classes'].append("only-light")
        dark_image_node['classes'].append("only-dark")

        # Insert dark image after light image
        index = figure_node.index(light_image_node)
        figure_node.insert(index + 1, dark_image_node)

        return node_list

#############################################################

def setup(app: Sphinx) -> None:
    app.add_directive("themed-figure", ThemedFigureDirective)
    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }

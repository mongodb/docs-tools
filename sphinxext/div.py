# Sourced from https://github.com/dnnsoftware/Docs/blob/master/common/ext/div.py

from docutils import nodes
from docutils.parsers.rst import Directive, directives
import sphinx


class DivNode(nodes.General, nodes.Element):
    def __init__(self, text):
        super(DivNode, self).__init__()

    @staticmethod
    def visit_div(self, node):
        self.body.append(self.starttag(node, 'div'))

    @staticmethod
    def depart_div(self, node=None):
        self.body.append('</div>\n')


class DivDirective(Directive):
    optional_arguments = 1
    final_argument_whitespace = True
    option_spec = {'name': directives.unchanged}
    has_content = True

    def run(self):
        self.assert_has_content()
        text = '\n'.join(self.content)
        try:
            if self.arguments:
                classes = directives.class_option(self.arguments[0])
            else:
                classes = []
        except ValueError:
            raise self.error(
                'Invalid class attribute value for "%s" directive: "%s".'
                % (self.name, self.arguments[0]))
        node = DivNode(text)
        node['classes'].extend(classes)
        self.add_name(node)
        self.state.nested_parse(self.content, self.content_offset, node)
        return [node]


def setup(app):
    app.add_node(DivNode, html=(DivNode.visit_div, DivNode.depart_div))
    app.add_directive('div', DivDirective)

    return {'parallel_read_safe': True,
            'parallel_write_safe': True}

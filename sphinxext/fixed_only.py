import logging
from docutils.parsers.rst import Directive, directives
from sphinx import addnodes
from sphinx.util.nodes import nested_parse_with_titles

logger = logging.getLogger('fasthtml')


class Cond(Directive):
    """
    Directive to only include text if the given tag(s) are enabled.
    """
    has_content = True
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {} # type: Dict

    def run(self):
        config = self.state.document.settings.env.config
        if config._raw_config['tags'].eval_condition(self.arguments[0]):
            # node = nodes.container()
            node = addnodes.only()
            node['expr'] = 'true'
            nested_parse_with_titles(self.state, self.content, node)
            # self.state.nested_parse(self.content, self.content_offset, node, match_titles=1)
            # include_lines = statemachine.string2lines(self.content, tab_width,
            #                                           convert_whitespace=True)
            # self.state_machine.insert_input(include_lines, path)
            return [node]

        return []


def setup(app):
    directives.register_directive('cond', Cond)

    return {
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }

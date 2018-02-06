import logging
from docutils import nodes
from docutils.parsers.rst import Directive, directives

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
            node = nodes.container()
            self.state.nested_parse(self.content, self.content_offset, node, match_titles=1)
            return [node]

        return []


def setup(app):
    directives.register_directive('cond', Cond)

    return {
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }

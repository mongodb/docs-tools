import os.path
import sys

from docutils import nodes, statemachine, utils
from docutils.utils.error_reporting import ErrorString
from docutils.parsers.rst import directives
from sphinx.util.compat import Directive

import json
import yaml


class TestCode(Directive):
    has_content = True
    required_arguments = 1
    optional_arguments = 1
    final_argument_whitespace = True
    option_spec = {}

    def run(self):
        language = self.arguments[0]

        first_line = [self.arguments[1]] if len(self.arguments) > 1 else []
        contents = u'\n'.join(first_line + list(self.content))
        defined_in = self.state.document.current_source
        source_path = self.state.document.get('source')

        try:
            data = yaml.safe_load(contents)
            if not isinstance(data, dict):
                raise self.severe(u'Expected YAML dictionary')

            code = data.get('code', '')
        except (yaml.scanner.ScannerError, yaml.parser.ParserError) as error:
            raise self.severe(u'Error parsing YAML:\n{}.'.format(ErrorString(error)))

        if not code:
            return []

        code = '\n'.join(['.. code-block:: javascript\n'] +
            ['   ' + line for line in code.split('\n')])

        rendered_lines = statemachine.string2lines(
            code, 4, convert_whitespace=1)
        self.state_machine.insert_input(rendered_lines, '')

        return []


def setup(app):
    app.add_directive('test', TestCode)

    return {'parallel_read_safe': True,
            'parallel_write_safe': True}

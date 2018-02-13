import fett
import re
from docutils.parsers.rst import Directive, directives
from docutils import statemachine
from docutils.utils.error_reporting import ErrorString

GUIDES_TEMPLATE = fett.Template('''
========================================================================
{{ title }}
========================================================================

.. default-domain:: mongodb

.. contents:: On this page
   :local:
   :backlinks: none
   :depth: 1
   :class: singlecol

{{ result_description }}

*Time required: {{ time }} minutes*

Prerequisites
-------------

{{ prerequisites }}

Procedure
---------

{{ if considerations }}
{{ considerations }}
{{ end }}

{{ procedure }}

Summary
-------

{{ summary }}

What's Next
-----------

{{ whats_next }}

''')

LEADING_WHITESPACE = re.compile(r'^\n?(\x20+)')
PAT_KEY_VALUE = re.compile(r'([a-z_]+):((?:[^\n]*\n)(?:^(?:\x20|\n)+[^\n]*\n?)*)', re.M)


def parse_keys(lines):
    """docutils field list parsing is busted. Just do this ourselves."""
    result = {}
    text = '\n'.join(lines).replace('\t', '    ')
    for match in PAT_KEY_VALUE.finditer(text):
        if match is None:
            continue

        value = match.group(2)
        indentation_match = LEADING_WHITESPACE.match(value)
        if indentation_match is None:
            value = value.strip()
        else:
            indentation = len(indentation_match.group(1))
            lines = [line[indentation:] for line in value.split('\n')]
            if lines[-1] == '':
                lines.pop()

            value = '\n'.join(lines)

        result[match.group(1)] = value

    return result


class Guide(Directive):
    has_content = True
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {}

    guide_keys = {
        'title': str,
        'author': str,
        'type': str,
        'level': str,
        'product_version': str,
        'result_description': str,
        'time': float,
        'prerequisites': str,
        'check_your_environment': str,
        'considerations': str,
        'procedure': str,
        'summary': str,
        'whats_next': str
    }

    guide_key_defaults = {
        'considerations': ''
    }

    def run(self):
        messages = []
        options = parse_keys(self.content)

        for key in self.guide_keys:
            if key not in options:
                if key in self.guide_key_defaults:
                    options[key] = self.guide_key_defaults[key]
                else:
                    messages.append(
                        self.state.document.reporter.warning(
                            'Missing required guide option: {}'.format(key),
                            line=self.lineno))

        try:
            rendered = GUIDES_TEMPLATE.render(options)
        except Exception as error:
            raise self.severe('Failed to render template: {}'.format(ErrorString(error)))

        rendered_lines = statemachine.string2lines(
            rendered, 4, convert_whitespace=1)
        self.state_machine.insert_input(rendered_lines, '')

        return messages


def setup(app):
    directives.register_directive('guide', Guide)

    return {
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }

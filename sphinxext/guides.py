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

Author: {{ author }}

{{ result_description }}

*Time required: {{ time }} minutes*

What You'll Need
----------------

{{ prerequisites }}

Check Your Environment
----------------------

{{ check_your_environment }}

Procedure
---------

{{ if considerations }}
{{ considerations }}
{{ end }}

{{ procedure }}

{{ if verify }}
Verify
------

{{ verify }}
{{ end }}

Summary
-------

{{ summary }}

What's Next
-----------

{{ whats_next }}
''')

LEADING_WHITESPACE = re.compile(r'^\n?(\x20+)')


class ParseError(Exception):
    def __init__(self, msg, lineno):
        super(ParseError, self).__init__(msg)
        self.lineno = lineno


def parse_keys(lines):
    """docutils field list parsing is busted. Just do this ourselves."""
    result = {}
    in_key = True
    indentation = 0

    pending_key = ''
    pending_value = []

    # This is a 2-state machine
    for lineno, line in enumerate(lines):
        line = line.replace('\t', '    ')
        line_indentation_match = LEADING_WHITESPACE.match(line)

        if not in_key:
            if line_indentation_match is None:
                if not line:
                    pending_value.append('')
                    continue

                # Switch to in_key
                result[pending_key] = '\n'.join(pending_value).strip()
                pending_value = []
                pending_key = ''
                in_key = True
                indentation = 0
            else:
                line_indentation = len(line_indentation_match.group(0))
                if indentation == 0:
                    indentation = line_indentation
                if line_indentation < indentation:
                    raise ParseError('Improper dedent', lineno)
                line_indentation = min(indentation, line_indentation)
                line = line[line_indentation:]
                pending_value.append(line)

        if in_key:
            if line_indentation_match is not None:
                raise ParseError('Unexpected indentation', lineno)

            parts = line.split(':', 1)
            if line.strip() and len(parts) != 2:
                raise ParseError('Expected key', lineno)

            pending_key = parts[0].strip()
            value = parts[1].strip()
            if value:
                pending_value.append(value)

            in_key = False

    if pending_value:
        result[pending_key] = '\n'.join(pending_value).strip()

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
        'verify': str,
        'summary': str,
        'whats_next': str,
        'seealso': str
    }

    guide_key_defaults = {
        'considerations': '',
        'verify': ''
    }

    def run(self):
        messages = []

        try:
            options = parse_keys(self.content)
        except ParseError as err:
            return [self.state.document.reporter.error(
                        str(err),
                        line=(self.lineno + err.lineno + 1))]

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


def test():
    """Test the parser"""
    parsed = '''title: Importing Data Into MongoDB
product_version: 3.6
  .. uriwriter:: hi
result_description:

  You can bulk import data into MongoDB using the ``mongoimport`` command distributed with the server.
  This guide will show you how.

time: 15
prerequisites:
  .. include:: /includes/steps/prereqs_crud.rst
summary:
  If you have successfully completed this guide, you have imported your first mongoDB data.
   Now in the next guide, you will retrieve the information you just imported.
seealso:
  stuff
  '''.split('\n')

    assert parse_keys(parsed) == {
        'title': 'Importing Data Into MongoDB',
        'product_version': '3.6\n.. uriwriter:: hi',
        'result_description': 'You can bulk import data into MongoDB using the ``mongoimport`` command distributed with the server.\nThis guide will show you how.',
        'time': '15',
        'prerequisites': '.. include:: /includes/steps/prereqs_crud.rst',
        'summary': 'If you have successfully completed this guide, you have imported your first mongoDB data.\n Now in the next guide, you will retrieve the information you just imported.',
        'seealso': 'stuff'}


if __name__ == '__main__':
    test()

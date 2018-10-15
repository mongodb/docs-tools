from docutils import statemachine
from docutils.nodes import Element, Text
from docutils.parsers.rst import Directive, directives
from template import populate, Options
import sphinx
import fett
import yaml

TAB_CONTENT_TEMPLATE = fett.Template('''
.. {{ tabset }}::

   hidden: true
   tabs:
     - id: {{ tab_id }}
       content: |
         {{ content }}
''')

TAB_BAR_TEMPLATE = fett.Template('''
.. {{ tabset }}::

   tabs:
   {{ for tab in tabs }}
     - id: {{ tab }}
       content: ""

   {{ end }}
''')


class TabBar(Directive):
    has_content = False
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {
        'tab-ids': directives.unchanged_required
    }

    def run(self):
        tabset = self.arguments[0]
        tabs = [id.strip() for id in self.options['tab-ids'].split(",")]

        rendered = TAB_BAR_TEMPLATE.render({
            "tabset": tabset,
            "tabs": tabs,
        })
        rendered_lines = statemachine.string2lines(
            rendered, 4, convert_whitespace=1
        )
        self.state_machine.insert_input(rendered_lines, '')

        return []


class TabContent(Directive):
    has_content = True
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {
        'tab-id': directives.unchanged_required
    }

    def run(self):
        options = self.options
        tabset = self.arguments[0]
        content = "\n".join(self.content)

        rendered = TAB_CONTENT_TEMPLATE.render({
            "tabset": tabset,
            "tab_id": options.get("tab-id"),
            "content": content
        })
        rendered_lines = statemachine.string2lines(
            rendered, 4, convert_whitespace=1
        )
        self.state_machine.insert_input(rendered_lines, '')

        return []


def setup(app):
    app.add_directive('tab-bar', TabBar)
    app.add_directive('tab-content', TabContent)

    return {'parallel_read_safe': True,
            'parallel_write_safe': True}

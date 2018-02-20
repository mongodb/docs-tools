from docutils import statemachine
from docutils.parsers.rst import Directive
import fett

CODEPEN_TEMPLATE = fett.Template('''
.. raw:: html

   <p class="codepen"
      data-pen-title="{{ slug escape }}"
      data-slug-hash="{{ slug escape }}"
      data-height="600"
      data-theme-id="32535"
      data-default-tab="js,result"
      data-user="mongodb-docs"
      data-embed-version="2"
      data-editable="true">
     <a href="https://codepen.io/mongodb-docs/pen/{{ slug escape }}">See this example on codepen: {{ slug escape }}</a>
   </p>
''')


class CodepenDirective(Directive):
    has_content = False
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True

    def run(self):
        data = {'slug': self.arguments[0]}
        rendered = CODEPEN_TEMPLATE.render(data)
        rendered_lines = statemachine.string2lines(
            rendered, 4, convert_whitespace=1)
        self.state_machine.insert_input(rendered_lines, '')

        return []


def setup(app):
    app.add_directive('codepen', CodepenDirective)

    return {
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }

from docutils import statemachine
from docutils.parsers.rst import Directive
from docutils.parsers.rst import directives
import fett

CODEPEN_TEMPLATE = fett.Template('''
.. raw:: html

   <iframe
     height={{ height }}
     scrolling='no'
     title={{ title escape }}
     src='//codepen.io/mongodb-docs/embed/{{ slug escape }}/?height={{ height }}&theme-id=32535&default-tab=js,result&embed-version=2&editable=true'
     frameborder='no'
     allowtransparency='true'
     allowfullscreen='true'
     style='width: 100%;'
   >   
     See the Pen
     <a href='https://codepen.io/mongodb-docs/pen/{{ slug escape }}/'>
       {{ title escape }}
     </a>
     by Shannon Bradshaw (<a href='https://codepen.io/mongodb-docs'>@mongodb-docs</a>)
     on <a href='https://codepen.io'>CodePen</a>.
   </iframe>

''')


class CodepenDirective(Directive):
    has_content = False
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {
        'height': directives.nonnegative_int,
        'title': directives.unchanged,
    }

    def run(self):
        options = self.options
        data = {
            'slug': self.arguments[0],
            'height': 600,
            'title': "MongoDB Stitch Example"
        }
        if options.get('height'):
            data['height'] = options['height']
        if options.get('title'):
            data['title'] = options['title']

        rendered = CODEPEN_TEMPLATE.render(data)
        rendered_lines = statemachine.string2lines(
            rendered, 4, convert_whitespace=1
        )
        self.state_machine.insert_input(rendered_lines, '')

        return []


def setup(app):
    app.add_directive('codepen', CodepenDirective)

    return {
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }

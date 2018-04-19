from docutils import statemachine
from docutils.parsers.rst import Directive
import re
import fett
import yaml
import template

# {{ for card in cards %FILTER% }}

CARD_GROUP_TEMPLATE = '''
.. raw:: html
   
   <div class="card_group">
     {{ for card in cards }}
       <div class="card card-large" role="button">
         <a href="{{ card.link }}">
           <div class="card-image">
               <img draggable="false" src="{{ card.image }}" />
           </div>
           <div class="card-content">
               {{ card.headline }}
           </div>
         </a>
       </div>
     {{ end }}
   </div>
'''


def process_yaml(contents):
    data = yaml.load(contents)
    return data


class CardGroup(Directive):
    has_content = True
    required_arguments = 0
    optional_arguments = 1
    final_argument_whitespace = True

    def run(self):
        data = process_yaml(self.content)
        rendered = CARD_GROUP_TEMPLATE.render(data)
        rendered_lines = statemachine.string2lines(
            rendered, 4, convert_whitespace=1
        )
        self.state_machine.insert_input(rendered_lines, '')

        return []


def setup(app):
    # app.add_directive('card-group', CardGroup)
    app.add_directive('card-group', template.create_directive(
        'card-group', CARD_GROUP_TEMPLATE, template.BUILT_IN_PATH, True))

    return {'parallel_read_safe': True,
            'parallel_write_safe': True}

from docutils import statemachine, utils, nodes
from docutils.parsers.rst import Directive, directives
from template import populate, Options
import sphinx
import re
import fett
import logging
import yaml
import json
import template

CARD_GROUP_TEMPLATE_LARGE = fett.Template('''
.. raw:: html
   
   <div class="card_group">
     {{ for card in cards }}
       <div class="card card-large" role="button" id="{{ card.id }}">
         <a href="{{ card.link }}">
           <div class="card-image">

.. image:: {{ card.image }}

.. raw:: html
   
           </div>
           <div class="card-content">
               {{ card.headline }}
           </div>
         </a>
       </div>
     {{ end }}
   </div>
''')


def process_doc_link(doc_link, env):
    return doc_link
    _, doc_path = env.relfn2path(doc_link)
    doc_path = utils.relative_path(None, doc_path)
    doc_path = nodes.reprunicode(doc_path)
    return doc_path


class CardGroup(Directive):
    has_content = True
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = True

    option_spec = {
        'type': lambda argument: directives.choice(argument,
                                                   ('large', 'small', None))
    }

    def process_data(self, data):
        env = self.state.document.settings.env
        cards = [
            dict(card, **{'link': process_doc_link(card['link'], env)})
            for card in data['cards']
        ]
        data['cards'] = cards

        return data

    def process_yaml(self, contents):
        source_path = self.state_machine.input_lines.source(
            self.lineno - self.state_machine.input_offset - 1)
        try:
            data = yaml.safe_load(contents)
        except yaml.YAMLError as error:
            raise self.severe(
                u'Error parsing YAML:\n{}.'.format(ErrorString(error)))
        options = Options(self.state, source_path, data)

        try:
            populate(data, options)
        except IOError as error:
            raise self.severe(u'Problems with "{}" directive path:\n{}.'.format(
                self.name, ErrorString(error)))

        return data

    def run(self):
        options = self.options
        card_type = str(options.get('type'))
        # Process the card group yaml body
        content = "\n".join(list(self.content))
        data = self.process_data(self.process_yaml(content))
        # Render the cards
        if card_type == "large":
            rendered = CARD_GROUP_TEMPLATE_LARGE.render(data)

            rendered_lines = statemachine.string2lines(
                rendered, 4, convert_whitespace=1
            )
            self.state_machine.insert_input(rendered_lines, '')

        return []


def setup(app):
    app.add_directive('card-group', CardGroup)

    return {'parallel_read_safe': True,
            'parallel_write_safe': True}

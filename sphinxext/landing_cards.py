from docutils import statemachine
from docutils.nodes import Element, Text
from docutils.parsers.rst import Directive, directives
from template import populate, Options
import sphinx
import fett
import yaml

CARD_GROUP_TEMPLATE_LARGE = fett.Template('''
.. raw:: html

   <div class="card_group">

     {{ for card in cards }}
     <a href="{{ card.link }}" class="card card-large" id="{{ card.id }}">
       <div class="card-image">

.. image:: {{ card.image }}

.. raw:: html

       </div>
       <div class="card-content">
         <div class="card-headline">{{ card.headline }}</div>
         {{if card.has_subheadline }}
         <div class="card-subheadline">{{ card.subheadline }}</div>
         {{end}}
       </div>
     </a>
     {{ end }}

   </div>
''')

CARD_GROUP_TEMPLATE_SMALL = fett.Template('''
.. raw:: html

    <div class="card_group">

      {{ for card in cards }}
      <a href="{{ card.link }}"
         class="card card-small"
      >
        <div class="card-icon">

.. image:: {{ card.icon }}

.. raw:: html

       </div>
       <div class="card-content">{{ card.headline }}</div>
     </a>
     {{ end }}
   </div> <!-- end card_group -->
''')


def process_card_data_field(card, field, fn):
    return dict(card, **{field: fn(card[field])})


def process_doc_link(doc_link):
    ''' TODO - convert role style links to relative paths
        e.g. given ":doc:`/procedure/init-stitchclient`"
             returns "http://docs.mongodb.com/stitch/procedure/init-stitchclient"
    '''
    return doc_link


class CardGroup(Directive):
    has_content = True
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {
        'type': lambda type: directives.choice(type, ('large', 'small', None))
    }

    def get_data(self):
        content = "\n".join(list(self.content))
        data = self.process_yaml(content)

        # Data post-processing
        cards = list(data["cards"])
        for card in cards:
            process_card_data_field(card, "link", process_doc_link)
            card["has_subheadline"] = bool(card.get('subheadline', False))
        data["cards"] = cards

        return data

    def process_yaml(self, contents):
        '''
        YAML processing from create_directive's custom class in template.py
        '''
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

    def render_cards(self, data, card_type):
        fett_templates = {
            "large": CARD_GROUP_TEMPLATE_LARGE,
            "small": CARD_GROUP_TEMPLATE_SMALL
        }
        if card_type in fett_templates.keys():
            rendered = fett_templates[card_type].render(data)
            rendered_lines = statemachine.string2lines(
                rendered, 4, convert_whitespace=1
            )
            self.state_machine.insert_input(rendered_lines, '')

    def run(self):
        options = self.options
        data = self.get_data()
        card_type = str(options.get('type', ''))

        self.render_cards(data, card_type)
        return []


def setup(app):
    app.add_directive('card-group', CardGroup)

    return {'parallel_read_safe': True,
            'parallel_write_safe': True}

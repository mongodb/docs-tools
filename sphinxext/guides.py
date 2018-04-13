from collections import namedtuple, OrderedDict
import re
import fett
from docutils.parsers.rst import Directive, directives
from docutils import statemachine
from docutils.utils.error_reporting import ErrorString
from sphinx import addnodes
from sphinx.util.nodes import set_source_info

# Set up our languages list, and override a couple long-winded entries
from tabs import LANGUAGES
LANGUAGES_IDS = [lang[0] for lang in LANGUAGES]
LANGUAGES_DICT = dict(LANGUAGES)
LANGUAGES_DICT['shell'] = 'Shell'

GuideCategory = namedtuple('GuideCategory', ('title', 'titlecssclass'))

GUIDE_DIRECTIVE_PATTERN = re.compile(r'''
    (?P<outer_indentation>\x20*)
    \.\. \x20 guide::\n
    (?:(?:(?P=outer_indentation) [^\n]+\n)|\n)*''', re.X)
LEADING_WHITESPACE = re.compile(r'^\n?(\x20+)')
GUIDE_CATEGORIES = {
    'Getting Started': GuideCategory('Getting Started', 'guide-category__title--getting-started'),
    'Use Case': GuideCategory('Use Case', 'guide-category__title--use-case'),
    'Deep Dive': GuideCategory('Deep Dive', 'guide-category__title--deep-dive')
}
GUIDES_TEMPLATE = fett.Template('''
:tocdepth: 2

====================================================================================================
{{ title }}
====================================================================================================

.. default-domain:: mongodb

{{ if languages }}
.. raw:: html

   <div class="guide-prefs">
   <div class="guide-prefs__caption">Language: <span class="show-current-language"></span></div>

.. tabs-pillstrip:: languages

.. raw:: html

   </div>
   <hr>

{{ end }}

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

{{ if whats_next }}

Next Guide:
-----------

.. container:: next-guide-box

   .. container:: next-guide-box-title

      {{ whats_next.title }}

   {{ whats_next.introduction }}

   .. raw:: html

      <a class="green-button" href="{{ whats_next.url }}">Next Guide</a>
{{ end }}

{{ if seealso }}

See Also:
---------

{{ seealso }}
{{ end }}
''')
GUIDES_INDEX_TEMPLATE = fett.Template('''
.. raw:: html

   {{ for category in categories }}
   <section class="guide-category">
     <div class="guide-category__title {{ category.titlecssclass }}">
       {{ category.title }}
     </div>
     {{ if category.truncated }}
       <div class="guide-category__view-all">View All Guides &gt;</div>
     {{ end }}
     <div class="guide-category__guides">
     {{ for column in category.columns }}
       <div class="guide-column">
       {{ for card in column }}
         {{ if card.jumbo }}
         <div class="guide guide--jumbo">
           <div class="guide__title">{{ card.title }}</div>
           <ol class="guide__body">
           {{ for guide in card.guides }}
             <li class="guide__entry"><a href="{{ guide.docname }}{{ link_suffix }}">{{ guide.title }}</a></li>
           {{ end }}
           </ol>
         </div>
         {{ else }}
         <a class="guide" href="{{ card.docname }}{{ link_suffix }}">
           <div class="guide__title">{{ card.title }}</div>
           <div class="guide__body"></div>
           <ul class="guide__pills">
           {{ for lang in card.card_languages }}
             <li class="guide__pill" data-tab-preference="{{ lang.id asIdentifier }}">{{ lang.title }}</li>
           {{ end }}
           {{ if card.languages_truncated }}
             <li class="guide__pill guide__pill--seeall">See All</li>
           {{ end }}
           </ul>
           <div class="guide__time">{{ card.time }}min</div>
         </a>
         {{ end }}
       {{ end }}
       </div>
     {{ end }}
     </div>
   </section>
   {{ end }}
''')


def validate_guide_category(guide_category):
    """Raise an error if guide_category is not a valid type of guide."""
    if guide_category not in GUIDE_CATEGORIES:
        raise ValueError('Invalid guide type')

    return guide_category


def validate_languages(languages):
    """Raise an error if an unknown tab language is used."""
    languages = languages.split()
    try:
        languages.sort(key=lambda lang_id: LANGUAGES_IDS.index(lang_id))
    except ValueError as err:
        raise ValueError('Unknown language "{}"'.format(err.message.split()[0]))

    return languages


def parse_whats_next(whats_next):
    lines = whats_next.strip().split('\n')
    if len(lines) != 3:
        raise ValueError('whats_next must be three lines')

    return {
        'title': lines[0],
        'introduction': lines[1],
        'url': lines[2]
    }


class ParseError(Exception):
    def __init__(self, msg, lineno):
        super(ParseError, self).__init__(msg)
        self.lineno = lineno


def parse_indentation(lines):
    """For each line, yield the tuple (indented, lineno, text)."""
    indentation = 0

    for lineno, line in enumerate(lines):
        line = line.replace('\t', '    ')
        line_indentation_match = LEADING_WHITESPACE.match(line)

        if line_indentation_match is None:
            yield (False, lineno, line)
            indentation = 0
        else:
            line_indentation = len(line_indentation_match.group(0))
            if indentation == 0:
                indentation = line_indentation

            if line_indentation < indentation:
                raise ParseError('Improper dedent', lineno)
            line_indentation = min(indentation, line_indentation)
            yield (True, lineno, line[line_indentation:])


def parse_keys(lines):
    """docutils field list parsing is busted. Just do this ourselves."""
    result = {}
    in_key = True

    pending_key = ''
    pending_value = []

    # This is a 2-state machine
    for is_indented, lineno, line in parse_indentation(lines):
        if not in_key:
            if not is_indented:
                if not line:
                    pending_value.append('')
                    continue

                # Switch to in_key
                result[pending_key] = '\n'.join(pending_value).strip()
                pending_value = []
                pending_key = ''
                in_key = True
            else:
                pending_value.append(line)

        if in_key:
            if is_indented:
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


class GuideDirective(Directive):
    has_content = True
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {}

    guide_keys = {
        'title': str,
        'languages': validate_languages,
        'author': str,
        'type': validate_guide_category,
        'level': str,
        'product_version': str,
        'result_description': str,
        'time': int,
        'prerequisites': str,
        'check_your_environment': str,
        'considerations': str,
        'procedure': str,
        'verify': str,
        'summary': str,
        'whats_next': str,
        'seealso': str
    }

    optional_keys = {
        'considerations',
        'verify',
        'languages',
        'whats_next',
        'seealso'
    }

    def run(self):
        messages = []

        try:
            options = parse_keys(self.content)
        except ParseError as err:
            return [self.state.document.reporter.error(
                        str(err),
                        line=(self.lineno + err.lineno + 1))]

        for key, validation_function in self.guide_keys.items():
            if key not in options:
                if key in self.optional_keys:
                    options[key] = ''
                else:
                    messages.append(
                        self.state.document.reporter.warning(
                            'Missing required guide option: {}'.format(key),
                            line=self.lineno))
                    continue

            try:
                options[key] = validation_function(options[key])
            except ValueError as err:
                message = 'Invalid guide option value: {}'.format(key)
                if err.message:
                    message += ': {}'.format(err.message)

                return [self.state.document.reporter.error(message, line=self.lineno)]

        # Parse specific values
        try:
            options['whats_next'] = parse_whats_next(options['whats_next'])
        except ValueError as err:
            options['whats_next'] = {}
            messages.append(
                self.state.document.reporter.warning(
                    'Error parsing whats_next: {}'.format(err.message),
                    line=self.lineno))

        try:
            rendered = GUIDES_TEMPLATE.render(options)
        except Exception as error:
            raise self.severe('Failed to render template: {}'.format(ErrorString(error)))

        rendered_lines = statemachine.string2lines(rendered, 4, convert_whitespace=1)
        self.state_machine.insert_input(rendered_lines, '')

        env = self.state.document.settings.env
        if not hasattr(env, 'guide_all_guides'):
            env.guide_all_guides = []

        guide = {
            'docname': env.docname,
            'title': options['title'],
            'time': options['time'],
            'category': options['type'],
            'all_languages': [{
                'title': LANGUAGES_DICT[lang],
                'id': lang} for lang in options['languages']],
            'card_languages': [],
            'languages_truncated': False,
            'jumbo': False
        }

        total_length = 0
        for language in guide['all_languages']:
            if total_length > 50:
                guide['languages_truncated'] = True
                break

            total_length += len(language['title']) + 4
            guide['card_languages'].append(language)

        env.guide_all_guides.append(guide)

        return messages


class CardSet:
    def __init__(self):
        self.categories = OrderedDict()
        for category_id, category in GUIDE_CATEGORIES.items():
            self.categories[category_id] = {
                'truncated': False,
                'title': category.title,
                'titlecssclass': category.titlecssclass,
                'columns': [[], [], []],
                'n_guides': 0
            }

    def get_next_column(self, category_id):
        columns = self.categories[category_id]['columns']
        return min(columns, key=lambda col: sum(2 if el['jumbo'] else 1 for el in col))

    def add_guide(self, env, guide, parent_card=None):
        env.included.add(guide['docname'])
        self.get_next_column(guide['category']).append(guide)
        self.categories[guide['category']]['n_guides'] += 1

    def add_guides(self, env, guides, title):
        categories = {}
        for guide in guides:
            # env.included.add(guide['docname'])
            categories.setdefault(guide['category'], []).append(guide)

        for category_name, category_guides in categories.items():
            card = {
                'title': title,
                'jumbo': True,
                'guides': category_guides
            }

            self.get_next_column(category_name).append(card)
            self.categories[category_name]['n_guides'] += 1


class GuideIndexDirective(Directive):
    has_content = True
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {}

    def run(self):
        env = self.state.document.settings.env
        if not hasattr(env, 'guide_all_guides'):
            return []

        guides = {}
        for guide in env.guide_all_guides:
            guides[guide['docname']] = guide

        cardset = CardSet()

        previous_line = None
        pending_card = [None]

        def handle_single_guide():
            if pending_card[0] is None:
                if previous_line not in guides:
                    return

                guide = guides[previous_line]
                cardset.add_guide(env, guide)
            else:
                cardset_guides = [guides[docname] for docname in pending_card[0]['guides'] if docname in guides]
                cardset.add_guides(env, cardset_guides, pending_card[0]['title'])
                pending_card[0] = None

        for is_indented, lineno, line in parse_indentation(self.content):
            if not line:
                continue

            if is_indented:
                # A card containing multiple guides
                if pending_card[0] is None:
                    pending_card[0] = {
                        'title': previous_line,
                        'jumbo': False,
                        'guides': []
                    }

                pending_card[0]['guides'].append(line)
            elif previous_line is not None:
                # A card containing a single guide
                handle_single_guide()

            previous_line = line

        if previous_line is not None:
            handle_single_guide()

        try:
            rendered = GUIDES_INDEX_TEMPLATE.render({
                'categories': [cat for cat in cardset.categories.values() if cat['n_guides'] > 0],
                'link_suffix': env.app.builder.link_suffix
            })
        except Exception as error:
            raise self.severe('Failed to render template: {}'.format(ErrorString(error)))

        rendered_lines = statemachine.string2lines(rendered, 4, convert_whitespace=1)
        self.state_machine.insert_input(rendered_lines, '')

        # Add guides to the TOC
        subnode = addnodes.toctree()
        subnode['hidden'] = True
        subnode['glob'] = False
        subnode['includefiles'] = list(guides.keys())
        subnode['parent'] = env.docname
        subnode['entries'] = [(guide['title'], guide['docname']) for guide in guides.values()]
        set_source_info(self, subnode)

        return [subnode]


def merge_info(app, env, docnames, other):
    if not hasattr(other, 'guide_all_guides'):
        return

    if not hasattr(env, 'guide_all_guides'):
        env.guide_all_guides = []

    env.guide_all_guides.extend(other.guide_all_guides)


def purge_guide_info(app, env, docname):
    if not hasattr(env, 'guide_all_guides'):
        return

    env.guide_all_guides = [
        guide for guide in env.guide_all_guides if guide['docname'] != docname
    ]


def setup(app):
    directives.register_directive('guide', GuideDirective)
    directives.register_directive('guide-index', GuideIndexDirective)
    app.connect('env-merge-info', merge_info)
    app.connect('env-purge-doc', purge_guide_info)

    return {
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }


def test_keyvalue():
    """Test the key/value parser"""
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
    test_keyvalue()

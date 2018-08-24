from docutils import statemachine
from docutils.parsers.rst import Directive, directives
from template import populate, Options
import yaml
import datetime
from dateutil.parser import parse as parse_date
import fett

STITCH_RELEASE = fett.Template('''
{{header}}
------------------------------------

{{for category in categories}}

.. _release-note-{{slug_date}}-{{category.name}}:

{{category.name}}
    {{for item in category.items}}
    - {{item.note}}
    {{if item.details}}

      {{item.details}}
    {{end}}

    {{end}}

{{end}}
.. raw:: html

   <br>
''')


def convert_to_snake_case(input):
    if type(input) is not str:
        raise TypeError("Can only convert strings to snake case.")
    return "_".join([part.lower() for part in input.split("-")])


class ReleaseItem:
    def __init__(self, **kwargs):
        # Data about this line item's parent section
        self.category = kwargs.get('category')
        # Data for this line item
        self.note = kwargs.get('note')
        self.details = kwargs.get('details')
        self.release_type = kwargs.get('release_type')
        self.jira_issue = kwargs.get('jira_issue')

        if not self.note or not self.category:
            raise TypeError("Release Item must have note and category.")

    def __repr__(self):
        return str(self.asdict())

    @staticmethod
    def parse(category, item):
        if type(item) is str:
            return ReleaseItem(category="Default", note=item)
        elif type(item) is dict:
            item = {convert_to_snake_case(prop): value
                    for prop, value in item.items()}
            return ReleaseItem(category=category, **item)
        else:
            raise TypeError("Invalid release item.")

    def asdict(self):
        return {
            "category": self.category,
            "note": self.note,
            "details": self.details,
            "release_type": self.release_type,
            "jira_issue": self.jira_issue
        }


class ReleaseCategory:
    def __init__(self, category, items):
        self.category = category
        self.items = [ReleaseItem.parse(category, item) for item in items]

    def asdict(self):
        return {
            "name": self.category,
            "items": [item.asdict() for item in self.items],
        }


class StitchRelease(Directive):
    has_content = True
    final_argument_whitespace = True
    required_arguments = 1
    optional_arguments = 0
    option_spec = {
        'fix-version': directives.unchanged,
    }

    def process_content(self, content):
        content = "\n".join(list(content))
        try:
            content = yaml.safe_load(content)
        except yaml.YAMLError as error:
            raise self.severe(
                u'Error parsing YAML:\n{}.'.format(ErrorString(error)))
        return content

    def render(self, release_date, release_content):
        rendered_stitch_release_template = STITCH_RELEASE.render({
            "header": release_date,
            "slug_date": parse_date(release_date).isoformat().split("T")[0],
            "categories": [ReleaseCategory(category, items).asdict()
                           for category, items in release_content.items()],
        })
        rendered_rst_lines = statemachine.string2lines(
            rendered_stitch_release_template, 4, convert_whitespace=1
        )
        self.state_machine.insert_input(rendered_rst_lines, '')

    def run(self):
        release_date = self.arguments[0]
        release_content = self.process_content(self.content)
        self.render(release_date, release_content)

        return []


def setup(app):
    app.add_directive('stitch-release', StitchRelease)

    return {'parallel_read_safe': True,
            'parallel_write_safe': True}

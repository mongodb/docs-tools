import re
import fett
import template
import docutils.nodes
import docutils.parsers.rst
from docutils.utils.error_reporting import ErrorString

PAT_RST_SECTION = re.compile(r'(.*)\n((?:^----+$)|(?:^====+$)|(?:^~~~~+$)|(?:^````+$))', re.M)
PAT_IDENTIFIER_ILLEGAL = re.compile(r'[^_0-9a-z]', re.I)

LANGUAGES = [('shell', 'Mongo Shell'),
             ('compass', 'Compass'),
             ('python', 'Python'),
             ('java-sync', 'Java (Sync)'),
             ('nodejs', 'Node.js'),
             ('php', 'PHP'),
             ('motor', 'Motor'),
             ('java-async', 'Java (Async)'),
             ('c', 'C'),
             ('cpp', 'C++11'),
             ('csharp', 'C#'),
             ('perl', 'Perl'),
             ('ruby', 'Ruby'),
             ('scala', 'Scala'),
             ('go', 'Go')]

DEPLOYMENTS = [('cloud', 'Cloud (Atlas)'),
               ('local', 'Local Instance')]

TABS_TOP = '''
.. raw:: html

   <div class="tabs-top"></div>
'''

PILLS_TEMPLATE = '''
.. raw:: html

   <ul class="guide__pills pillstrip-declaration" role="tablist" data-tab-preference="{{ title }}"></ul>
'''

TABS_TEMPLATE = '''
.. raw:: html

   <div class="tabs" %PREFERENCE%>
     {{ if hidden not }}
     <ul class="tab-strip tab-strip--singleton" role="tablist">
       {{ for tab in tabs %FILTER% }}
       {{ # Only render the tab here if i < 5 }}
       {{ if i lessThan(5) }}
       <li class="tab-strip__element" data-tabid="{{ tab.id asIdentifier }}" role="tab" aria-selected="{{ if i zero }}true{{ else }}false{{ end }}">{{ tab.name }}</li>
       {{ end }}
       {{ end }}
       {{ if tabs len greaterThan(5) }}
       <li class="tab-strip__element dropdown">
         <a class="dropdown-toggle" data-toggle="dropdown">Other <span class="caret"></span></a>
         <ul class="dropdown-menu tab-strip__dropdown" role="menu">
           {{ for tab in tabs %FILTER% }}
           {{ # Only render the tab here if i >= 5 }}
           {{ if i greaterThanOrEqual(5) }}
           <li data-tabid="{{ tab.id asIdentifier }}" aria-selected="{{ if i zero }}true{{ else }}false{{ end }}">{{ tab.name }}</li>
           {{ end }}
           {{ end }}
         </ul>
       </li>
       {{ end }}
     </ul>
     {{ end }}
     <div class="tabs__content" role="tabpanel">
       {{ for tab in tabs %FILTER% }}
       <div class="tabpanel-{{ tab.id asIdentifier }}" data-tabid="{{ tab.id asIdentifier }}">

{{ tab.content convertSections }}

.. raw:: html

       </div>
       {{ end }}
     </div>
   </div>
'''

# Fix passing title from RST into HTML templates below
HEADING_TEMPLATE_RST = '''
.. h{}::

   title: |
     {}
'''

H1_TEMPLATE_HTML = '''
.. raw:: html

   <h1>{{ title }}</h1>
'''

H2_TEMPLATE_HTML = '''
.. raw:: html

   <h2>{{ title }}</h2>
'''

H3_TEMPLATE_HTML = '''
.. raw:: html

   <h3>{{ title }}</h3>
'''

H4_TEMPLATE_HTML = '''
.. raw:: html

   <h4>{{ title }}</h4>
'''


def option_bool(argument):
    """A docutils option validator for boolean flags."""
    if not argument:
        return 'true'
    return docutils.parsers.rst.directives.choice(argument, ('true', 'false'))


class tab(docutils.nodes.General, docutils.nodes.Element):
    """An instance of a tab. Has the following attributes:

       - tabid: optional id identifying the tab. Generated from title if needed.
       - title: optional title for the tab.
       - source: string source of the tab's contents.

       One of tabid or title must be provided."""
    pass


def build_template(tab_filter, preference):
    # If tab_filter is not a string, make it an empty string
    if not isinstance(tab_filter, str):
        tab_filter = ''

    template = TABS_TEMPLATE.replace('%FILTER%', tab_filter)

    if isinstance(preference, str) and preference != '':
        return template.replace('%PREFERENCE%', 'data-tab-preference="{}"'.format(preference))

    return template.replace('%PREFERENCE%', '')


def create_tab_directive(name, tab_definitions):
    """Create a tab directive with the given tabset name and list of
       (tabid, title) pairs for tab sorting and validation. For an
       anonymous tab directive, name and tab_definitions should both be
       empty."""
    # If this is a named tabset with a restricted set of tab IDs,
    # create a sorting function that the template can use
    if tab_definitions:
        tab_ids = [tab_definition[0] for tab_definition in tab_definitions]
        tab_display = [tab_definition[1] for tab_definition in tab_definitions]

        def sort_tabs(tab_data):
            # Create a list for the sorted data
            sorted_tabs = [None] * len(tab_definitions)

            for tab in tab_data:
                index = tab_ids.index(tab['id'])
                tab['name'] = tab_display[index]
                sorted_tabs[index] = tab

            return filter(None, sorted_tabs)

        sorter_name = 'sort' + name.title()
        fett.Template.FILTERS[sorter_name] = sort_tabs

    # Create a templated superclass for this tabs directive.
    LegacyDirective = template.create_directive(
        'tabs-{}'.format(name) if name else 'tabs',
        build_template(sorter_name if tab_definitions else '', name),
        template.BUILT_IN_PATH,
        True)

    class TabsDirective(LegacyDirective):
        """A set of tabbed content. This is complex: there's four possible states we
           handle:
           - Legacy (YAML) Syntax
           - Pure-RST Syntax
           and
           - Anonymous tabset
           - Named tabset"""
        optional_arguments = 1
        final_argument_whitespace = True
        has_content = True
        option_spec = {
            'tabset': str,
            'hidden': option_bool
        }

        def run(self):
            # Transform the old YAML-based syntax into the new pure-rst syntax.
            # This heuristic guesses whether we have the old syntax or the new.
            # Basically, if any of the first 2 non-empty lines are "tabs:", that's a good
            # signal that this is YAML. Why 2? One for hidden:..., one for tabs:.
            nonempty_lines = list(line for line in self.content if line)
            if any(line == 'tabs:' for line in nonempty_lines[:2]):
                return LegacyDirective.run(self)

            # Map the new syntax into structured data, and plug it into the old
            # template rendering.
            tabs_node = docutils.nodes.Element()
            tabs_node.source, tabs_node.line = self.state_machine.get_source_and_line(self.lineno)
            tabs_node.document = self.state.document
            data = {
                'hidden': self.options.get('hidden', 'false') == 'true',
                'tabs': []
            }

            self.state.nested_parse(
                self.content,
                self.content_offset,
                tabs_node,
                match_titles=True,
            )

            # Transform the rst nodes into structured data to plug into our template
            for node in tabs_node.children:
                if not isinstance(node, tab):
                    raise self.severe(ErrorString('"tabs" may only contain "tab" directives'))

                data['tabs'].append({
                    'id': node['tabid'],
                    'name': node['title'],
                    'content': node['source']
                })

            return self.render(data)

    return TabsDirective


class TabInstanceDirective(docutils.parsers.rst.Directive):
    """A single tab in a set of tabs. Contains a tabid, an optional title, and
       a chunk of rst content."""
    optional_arguments = 1
    final_argument_whitespace = True
    has_content = True
    option_spec = {
        'tabid': str,
    }

    def run(self):
        node = tab()
        node.source, node.line = self.state_machine.get_source_and_line(self.lineno)

        if not self.arguments and 'tabid' not in self.options:
            raise self.severe(ErrorString('Argument or tabid required for a tab'))

        title = self.arguments[0] if self.arguments else ''
        node['tabid'] = self.options.get('tabid', title)
        node['title'] = title
        node['source'] = '\n'.join(self.content)
        return [node]


def setup(app):
    # Handle headers inside tab directives
    app.add_directive('h1', template.create_directive('h1', H1_TEMPLATE_HTML, template.BUILT_IN_PATH, True))
    app.add_directive('h2', template.create_directive('h2', H2_TEMPLATE_HTML, template.BUILT_IN_PATH, True))
    app.add_directive('h3', template.create_directive('h3', H3_TEMPLATE_HTML, template.BUILT_IN_PATH, True))
    app.add_directive('h4', template.create_directive('h4', H4_TEMPLATE_HTML, template.BUILT_IN_PATH, True))

    # Create directive for positioning tabs at top of the page
    app.add_directive('tabs-top', template.create_directive('tabs-top', TABS_TOP, template.BUILT_IN_PATH, True))
    app.add_directive('tabs-pillstrip', template.create_directive('tabs-pillstrip', PILLS_TEMPLATE, template.BUILT_IN_PATH, False))

    # Create drivers tab directive
    app.add_directive('tabs-drivers',
        create_tab_directive('languages', LANGUAGES))
    app.add_directive('tabs-cloud',
        create_tab_directive('cloud', DEPLOYMENTS));

    # Create operating system tab directive
    app.add_directive('tabs-platforms',
        create_tab_directive('platforms',
            [('windows', 'Windows'),
             ('macos', 'macOS'),
             ('linux', 'Linux'),
             ('debian', 'Debian'),
             ('rhel', 'RHEL')]))

    # Create Stitch SDK tab directive
    app.add_directive(
        'tabs-stitch-sdks',
        create_tab_directive('stitchSdks', [ # Note: camelCase is required
            ('functions', 'Functions'),
            ('javascript', 'JavaScript SDK'),
            ('android', 'Android SDK'),
            ('ios', 'iOS SDK')
        ])
    )

    app.add_directive(
        'tabs-stitch-interfaces',
        create_tab_directive('stitchInterfaces', [
            ('stitch-ui', 'Stitch UI'),
            ('import-export', 'Import/Export')
        ])
    )

    app.add_directive(
        'tabs-stitch-auth-providers',
        create_tab_directive('stitchAuthProviders', [
            ('anon-user', 'Anonymous'),
            ('local-userpass', 'Email/Password'),
            ('oauth2-google', 'Google'),
            ('oauth2-facebook', 'Facebook'),
            ('api-key', 'API Key Authentication'),
            ('custom-token', 'Custom')
        ])
    )

    # Create auth tab directive
    app.add_directive('tabs-auth',
        create_tab_directive('auth',
            [('uidpwd', 'Username and Password'),
             ('ldap', 'LDAP'),
             ('kerberos', 'Kerberos')
        ])
    )

    # Create deployments tab directive
    app.add_directive('tabs-deployments',
        create_tab_directive('deployments',
            [('standalone', 'Standalone'),
             ('repl', 'Replica Set'),
             ('shard', 'Sharded Cluster')
        ])
    )

    # Create cloud providers tab directive
    app.add_directive('tabs-cloud-providers',
        create_tab_directive('cloudproviders',
            [('aws', 'AWS'),
             ('azure', 'Azure'),
             ('gcp', 'GCP')
        ])
    )

    # Create general purpose tab directive with no error checking
    app.add_directive('tabs', create_tab_directive('', []))

    # Add a tab directive used by the new tab syntax
    app.add_directive('tab', TabInstanceDirective)

    return {'parallel_read_safe': True,
            'parallel_write_safe': True}


def convert_sections(tab_content):
    """Convert rst-style sections into custom directives that ONLY insert
       the HTML header tags."""
    return PAT_RST_SECTION.sub(
        lambda match: HEADING_TEMPLATE_RST.format(template.Options.HEADING_LEVELS.index(match.group(2)[0]) + 1, match.group(1)),
        tab_content)


fett.Template.FILTERS['convertSections'] = convert_sections
fett.Template.FILTERS['asIdentifier'] = lambda val: PAT_IDENTIFIER_ILLEGAL.sub('', val)

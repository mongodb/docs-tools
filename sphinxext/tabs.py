import re
import fett
import template

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
             # ('cpp11', 'C++11'),
             ('csharp', 'C#'),
             ('perl', 'Perl'),
             ('ruby', 'Ruby'),
             ('scala', 'Scala')]

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
       <div class="tabpanel-{{ tab.id asIdentifier }}">

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

   title: {}
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


def build_template(tab_filter, preference):
    # If tab_filter is not a string, make it an empty string
    if not isinstance(tab_filter, str):
        tab_filter = ''

    template = TABS_TEMPLATE.replace('%FILTER%', tab_filter)

    if isinstance(preference, str) and preference != '':
        return template.replace('%PREFERENCE%', 'data-tab-preference="{}"'.format(preference))

    return template.replace('%PREFERENCE%', '')


def create_tab_directive(name, tab_definitions):
    tab_ids = [tab_definition[0] for tab_definition in tab_definitions]
    tab_display = [tab_definition[1] for tab_definition in tab_definitions]

    def sortTabs(tab_data):
        # Create a list for the sorted data
        sorted = [None] * len(tab_definitions)

        for tab in tab_data:
            index = tab_ids.index(tab['id'])
            tab['name'] = tab_display[index]
            sorted[index] = tab

        return filter(None, sorted)

    sorter_name = 'sort' + name.title()
    fett.Template.FILTERS[sorter_name] = sortTabs

    return template.create_directive(
        'tabs-{}'.format(name),
        build_template(sorter_name, name),
        template.BUILT_IN_PATH,
        True)


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

    # Create operating system tab directive
    app.add_directive('tabs-platforms',
        create_tab_directive('platforms',
            [('windows', 'Windows'),
             ('macos', 'macOS'),
             ('linux', 'Linux'),
             ('debian', 'Debian'),
             ('rhel', 'RHEL')]))

    # Create general purpose tab directive with no error checking
    app.add_directive('tabs', template.create_directive('tabs', build_template('', ''), template.BUILT_IN_PATH, True))

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

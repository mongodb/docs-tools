import re
import fett
import template

PAT_RST_SECTION = re.compile(r'(.*)\n((?:^----+$)|(?:^====+$)|(?:^~~~~+$)|(?:^````+$))', re.M)
# List of tuples with language tab ( ID, Display Name)
LANGUAGES_RAW = [('shell', 'Mongo Shell'),
             ('compass', 'Compass'),
             ('python', 'Python'),
             ('java-sync', 'Java (Sync)'),
             ('nodejs', 'Node.js'),
             ('php', 'PHP'),
             ('motor', 'Motor'),
             ('java-async', 'Java (Async)'),
             ('c', 'C'),
             #('cpp11', 'C++11'),
             ('csharp', 'C#'),
             ('perl', 'Perl'),
             ('ruby', 'Ruby'),
             ('scala', 'Scala')
             ]
LANGUAGES_IDS = [lang[0] for lang in LANGUAGES_RAW]
LANGUAGES_DISPLAY = [lang[1] for lang in LANGUAGES_RAW]

TABS_TOP = '''
.. raw:: html

   <div class="tabs-top"></div>
'''

TABS_TEMPLATE = '''
.. raw:: html

   <div class="tabs">
     {{ if hidden not }}
     <ul class="tab-strip tab-strip--singleton" role="tablist" %PREFERENCE%>
       {{ for tab in tabs %FILTER% }}
       {{ # Only render the tab here if i < 5 }}
       {{ if i lessThan(5) }}
       <li class="tab-strip__element" data-tabid="{{ tab.id }}" role="tab" aria-selected="{{ if i zero }}true{{ else }}false{{ end }}">{{ tab.name }}</li>
       {{ end }}
       {{ end }}
       {{ if tabs len greaterThan(5) }}
       <li class="tab-strip__element dropdown">
         <a class="dropdown-toggle" data-toggle="dropdown">Other <span class="caret"></span></a>
         <ul class="dropdown-menu tab-strip__dropdown" role="menu">
           {{ for tab in tabs %FILTER% }}
           {{ # Only render the tab here if i >= 5 }}
           {{ if i greaterThanOrEqual(5) }}
           <li data-tabid="{{ tab.id }}" aria-selected="{{ if i zero }}true{{ else }}false{{ end }}">{{ tab.name }}</li>
           {{ end }}
           {{ end }}
         </ul>
       </li>
       {{ end }}
     </ul>
     {{ end }}
     <div class="tabs__content" role="tabpanel">
       {{ for tab in tabs %FILTER% }}
       <div class="tabpanel-{{ tab.id }}">

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

def setup(app):
    # Handle headers inside tab directives
    directive = template.create_directive('h1', H1_TEMPLATE_HTML, template.BUILT_IN_PATH, True)
    app.add_directive('h1', directive)

    directive = template.create_directive('h2', H2_TEMPLATE_HTML, template.BUILT_IN_PATH, True)
    app.add_directive('h2', directive)

    directive = template.create_directive('h3', H3_TEMPLATE_HTML, template.BUILT_IN_PATH, True)
    app.add_directive('h3', directive)

    directive = template.create_directive('h4', H4_TEMPLATE_HTML, template.BUILT_IN_PATH, True)
    app.add_directive('h4', directive)

    # Create directive for positioning tabs at top of the page
    directive = template.create_directive('tabs-top', TABS_TOP, template.BUILT_IN_PATH, True)
    app.add_directive('tabs-top', directive)

    # Create drivers tab directive
    directive = template.create_directive('tabs-drivers', buildTemplate("sortLanguages", "drivers"), template.BUILT_IN_PATH, True)
    app.add_directive('tabs-drivers', directive)

    # Create general purpose tab directive with no error checking
    directive = template.create_directive('tabs', buildTemplate("", ""), template.BUILT_IN_PATH, True)
    app.add_directive('tabs', directive)

    return {'parallel_read_safe': True,
            'parallel_write_safe': True}

def buildTemplate(tabFilter, preference):
    # If tabFilter is not a string, make it an empty string
    if type(tabFilter) != str:
        tabFilter = ""
    template = TABS_TEMPLATE.replace("%FILTER%", tabFilter)

    if type(preference) == str and preference != "":
        template = template.replace("%PREFERENCE%", "data-tab-preference=\"" + preference + "\"")
    else:
        template = template.replace("%PREFERENCE%", "")

    return template

def convertSections(tabContent):
    """Convert rst-style sections into custom directives that ONLY insert
       the HTML header tags."""
    return PAT_RST_SECTION.sub(
        lambda match: HEADING_TEMPLATE_RST.format(template.Options.HEADING_LEVELS.index(match.group(2)[0]) + 1, match.group(1)),
        tabContent)

fett.Template.FILTERS['convertSections'] = convertSections

def getLanguageNames(tabData):
    for tab in tabData:
        index = LANGUAGES_IDS.index(tab['id'])
        tab['name'] = LANGUAGES_DISPLAY[index]

    return tabData

fett.Template.FILTERS['getLanguageNames'] = getLanguageNames

def sortLanguages(tabData):
    # Create a list for the sorted data
    sorted = [None] * len(LANGUAGES_RAW)

    for tab in tabData:
        index = LANGUAGES_IDS.index(tab['id'])
        tab['name'] = LANGUAGES_DISPLAY[index]
        sorted[index] = tab

    return filter(None, sorted)

fett.Template.FILTERS['sortLanguages'] = sortLanguages

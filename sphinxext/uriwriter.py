import fett
import re
from docutils.parsers.rst import Directive, directives
from docutils import statemachine
from docutils.utils.error_reporting import ErrorString


URIWRITER_TEMPLATE = fett.Template('''
.. raw:: html

   <p class="uriwriter">
   <form class="uriwriter" id="uriwriter" autocomplete="off">
     <div class="serverinfo">Select your server deployment type:</div>
     <div id="userinfo flex-container" class="row">
        <fieldset>
                <ul class="guide__pills">
                    <li class="guide__pill uriwriter_sel">self-managed MongoDB</li>
                    <li class="guide__pill uriwriter_sel">Atlas (Cloud) with shell v. 3.4</li>
                    <li class="guide__pill uriwriter_sel">Atlas (Cloud) with shell v. 3.6</li>
                    <li class="guide__pill uriwriter_sel">replica set</li>
                </ul>
        </fieldset>
        <fieldset>
            <input class="input-uriwriter" id="uriwriter_username" data-toggle="tooltip" title="username you will use to connect" type="text" name="username" required>
            <label class="label-uriwriter" for="username">Username</label>
        </fieldset>
        <fieldset>
            <input class="input-uriwriter" id="uriwriter_db" type="text" name="db" required>
            <label class="label-uriwriter" for="db">Database name</label>
        </fieldset>
        <div id="options"></div>
    </div>
     <div class="serverinfo">Add Servers:</div>
    <div class="flex-container">
       
        <fieldset class="hostgrid">
            <input class="input-uriwriter" id="hostname" type="text" name="hostname">
            <label for="hostname">Hostname or IP</label>
        </fieldset>
        <fieldset class="hostgrid">
            <input class="input-uriwriter" id="port" type="number" name="port">
            <label for="port">Port</label>
        </fieldset>
        <fieldset class="hostbutton">
            <button id="uriwriter_act">+</button>
        </fieldset>
    </div>
    </form>
    <div id="hostlistwrapper">
       <ul id="hostlist" style="list-style-type:none">
       </ul>
    </div>
   </p>
''')

URIWRITER_TEMPLATE_TARGET = fett.Template('''
.. raw:: html
   <div class="uri">URI_STRING</div>
''')



LEADING_WHITESPACE = re.compile(r'^\n?(\x20+)')
PAT_KEY_VALUE = re.compile(r'([a-z_]+):(.*)', re.M)




def parse_keys(lines):
    """docutils field list parsing is busted. Just do this ourselves."""
    result = {}
    text = '\n'.join(lines).replace('\t', '    ')
    print text
    for match in PAT_KEY_VALUE.finditer(text):
        if match is None:
            continue
        value = match.group(2)
        indentation_match = LEADING_WHITESPACE.match(value)
        if indentation_match is None:
            value = value.strip()
        else:
            indentation = len(indentation_match.group(1))
            lines = [line[indentation:] for line in value.split('\n')]
            if lines[-1] == '':
                lines.pop()

            value = '\n'.join(lines)

        result[match.group(1)] = value

    return result


class UriwriterDirective(Directive):
    has_content = True
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = True

    def run(self):
        print self.content
        options = parse_keys(self.content)
        print options
       
        if 'target' in options:
            rendered = URIWRITER_TEMPLATE_TARGET.render(options)
        else:
            rendered = URIWRITER_TEMPLATE.render(options)
       
        rendered_lines = statemachine.string2lines(
            rendered, 4, convert_whitespace=1)
        self.state_machine.insert_input(rendered_lines, '')

        return []


def setup(app):
    app.add_directive('uriwriter', UriwriterDirective)

    return {
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }

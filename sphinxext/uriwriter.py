import fett
import re
from docutils.parsers.rst import Directive, directives
from docutils import statemachine
from docutils.utils.error_reporting import ErrorString


URIWRITER_TEMPLATE = '''
.. raw:: html

   <form class="uriwriter__form" id="uriwriter" autocomplete="off">
       <div class="mongodb-form__prompt">
           <div class="mongodb-form__label">Server deployment type</div>
           <ul class="guide__pills">
               <li class="uriwriter__toggle guide__pill">on-premise MongoDB</li>
               <li class="uriwriter__toggle guide__pill">on-premise MongoDB with replica set</li>
               <li class="uriwriter__toggle guide__pill">Atlas (Cloud)</li>
           </ul>
       </div>
       <label class="mongodb-form__prompt uriwriter__atlascontrols">
           <div class="mongodb-form__label">Atlas connection string</div>
           <div>
               <textarea class="mongodb-form__input" id="uriwriter_atlaspaste" spellcheck=false rows="3" cols="50" placeholder='mongo "mongodb+srv://clustername.mongodb.net/test" --username user'></textarea>
               <div class="atlascontrols__status mongodb-form__status"></div>
           </div>
       </label>
       <div id="userinfo_form">
           <label class="mongodb-form__prompt">
               <div class="mongodb-form__label">Username</div>
               <input class="mongodb-form__input" id="uriwriter_username" required>
           </label>
           <label class="mongodb-form__prompt">
               <div class="mongodb-form__label">Database name</div>
               <input class="mongodb-form__input" id="uriwriter_db" required>
           </label>
           <div class="mongodb-form__prompt" data-server-configuration>
               <div class="mongodb-form__label">Servers</div>
               <div id="hostlist"></div>
           </div>
       </div>
   </form>
'''

class UriwriterDirective(Directive):
    has_content = True
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = True

    def run(self):
        rendered = URIWRITER_TEMPLATE
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

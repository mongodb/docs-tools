import template
from docutils.parsers.rst import Directive

ACCORDION_TEMPLATE = '''
.. raw:: html

   <div class="accordion accordion--collapsed">
     <div class="accordion__button" role="button">
       <span class="accordion__title">{{title}}</span>
       <span class="accordion__action">Expand</span>
     </div>

     <div class="accordion__content">

.. container::

   {{body}}

.. raw:: html

     </div>
   </div>
'''

class Accordion(Directive):
    """
    Directive expand and collapse content.
    """
    has_content = True
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {} # type: Dict

    def run(self):
        config = self.state.document.settings.env.config
        # self.arguments[0]

        return []


def setup(app):
    app.add_directive('accordion', template.create_directive('accordion', ACCORDION_TEMPLATE, template.BUILT_IN_PATH, False))

    return {
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }

import template

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


def setup(app):
    app.add_directive('accordion', template.create_directive('accordion', ACCORDION_TEMPLATE, template.BUILT_IN_PATH, False))

    return {
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }

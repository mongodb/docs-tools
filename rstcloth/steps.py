"""
Steps schema is:

{
  "title": <str>,
  "stepnum": <int>,
  "pre": <str>,
  "post": <str>,
  "ref": <str>,
  "action": {
               "heading": <str>,
               "code": <str>,
               "language": <str>,
               "content": <str>,
               "pre": <str>,
               "post": <str>
             }
}

Notes:

 - ref becomes a global link target, but has ``step-<num>-<file_name>-``
   prepended to it in source.

 - stepnum is optional. If not specified, we assume that the sequence starts at
   one. If you specify your own ``stepnum`` in one step you have to specify your
   own step number in all steps in this sequence. The script enforces order, so
   that if you specify stepnum, you don't need to specify steps in the source file in order.

 - "title" and "heading" fields can optionally hold a document that contains
   both a "text" field *and* a "character" field if you need to adjust the level
   of the heading. For example:

   {
     "title":
       {
         "text": "name of step",
         "character": "-"
       }
   }

   Therefore "name of step" is, by MongoDB docs convention an "h2". By default,
   heading within actions are h4s and titles of steps are h3s.

 - pre/post are optional. and allow you to add prefix or postfix text to a step
   or code example/action.

 - Action should be either a doc or a list of docs. Their fields are optional,
   with the following notable points:

   - "language" refers to the syntax highlighting of "code," and is unused
     otherwise.

   - "content" is a paragraph, for steps that don't have code examples.

 - the spec/agg format would be at least:

   {
     "source":
       {
         "file": <str>
         "ref":
       }
   }

   callers may specify ``description`` and ``title`` to override the source
   location. (ref needs to be modified in calling location.)

There are several situations where we raise errors because a step document is
invalid:

1. A step has both a "source" (i.e. is an included step), and an "action" field.

2. A code block contains both "content" and "code" fields.

"""

import yaml
import sys, os
from rstcloth import RstCloth
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'bin')))
from utils import ingest_yaml_list

class InvalidStep(Exception):
    pass

class Steps(object):
    """
    take the input file, ingest content to support spec/aggregated lists, and
    store in an internal representation.
    """
    def __init__(self, fn, cache=None):
        if cache is None:
            cache = dict()

        self.source_fn = fn
        self.agg_sources = cache
        self.source_list = ingest_yaml_list(self.source_fn)
        self.source = dict()

        sort_needed = False

        idx = 0
        for step in self.source_list:
            if 'stepnum' not in step:
                step['stepnum'] = idx+1
            else:
                sort_needed = True

            if 'source' in step:
                if 'action' in step:
                    raise InvalidStep
                source_file = step['source']['file']
                if source_file in self.agg_sources:
                    current_step = self.agg_sources[step['source']['file']][step['source']['ref']]
                else:
                    steps = Steps(source_file, self.agg_sources)
                    current_step = steps.get_step(step['source']['ref'])
                    self.agg_sources[source_file] = steps
                    self.agg_sources.update(steps.agg_sources)

                current_step.update(step)

                self.source_list[idx] = current_step
                self.source[step['source']['ref']] = current_step
            else:
                self.source[step['ref']] = step

            idx += 1

        if sort_needed is True:
            self.source_list.sort(key=lambda k:k['stepnum'])

    def get_step(self, ref):
        return self.source[ref]

class StepsOutput(object):
    """
    Base class for rendered step form. The render() method generates the rst in
    the internal RstCloth object.
    """

    def __init__(self, steps):
        if not isinstance(steps, Steps):
            raise TypeError
        else:
            self.steps = steps

        self.rst = RstCloth()
        self.hook()

    def hook(self):
        self.indent = 3

    def render(self):
        for step in self.steps.source_list:
            self.heading(step)

            self.pre(step)

            if isinstance(step['action'], list):
                for block in step['action']:
                    self.code_step(block)
            else:
                self.code_step(step['action'])

            self.post(step)

    def pre(self, doc):
        if 'pre' in doc:
            self.rst.content(doc['pre'], indent=self.indent)
            self.rst.newline()

    def post(self, doc, code_step=False):
        if 'post' in doc:
            self.rst.content(doc['post'], indent=self.indent)
            self.rst.newline()

        if code_step is False:
            self.post_step_hook()

    def post_step_hook(self):
        pass

    def _heading(self, block, override_char=None, indent=0):
        if 'heading' in block:
            if isinstance(block['heading'], dict):
                if 'character' in block['heading']:
                    pass
                else:
                    block['heading']['character'] = override_char
            else:
                block['heading'] = { 'text': block['heading'],
                                     'character': override_char }

            self.rst.heading(text=block['heading']['text'],
                             char=block['heading']['character'],
                             indent=indent)

            self.rst.newline()

    def code_step(self, block):
        if 'code' in block and 'content' in block:
            raise InvalidStep

        self.pre(block)

        self._heading(block, override_char='`', indent=self.indent)

        if 'code' in block:
            if 'language' not in block:
                block['language'] = 'none'

            self.rst.directive(name='code-block',
                               arg=block['language'],
                               content=block['code'],
                               indent=self.indent)
            self.rst.newline()

        if 'content' in block:
            self.content(block['content'], indent=self.indent)

        self.post(block, code_step=True)

    def key_name(self):
        key_name = os.path.splitext(os.path.basename(self.steps.source_fn))[0]
        if key_name.startswith('step-') or key_name.startswith('steps-'):
            key_name = key_name.split('-', 1)[1]

        return key_name

class PrintStepsOutput(StepsOutput):
    """
    Variant of Steps class for generating latex-appropriate content that won't
    depend on CSS.
    """

    def hook(self):
        self.indent = 0

    def heading(self, doc):
        self.rst.ref_target('step-{0}-{1}-{2}'.format(doc['stepnum'],
                                                      self.key_name(),
                                                      doc['ref']))
        self.rst.newline()

        self._heading(block={ 'heading': "Step {0}: {1}".format(str(doc['stepnum']), doc['title']) },
                      override_char='~',
                      indent=self.indent)

class WebStepsOutput(StepsOutput):
    """
    Variant of Steps class for generating web-content that depends on CSS
    classes.
    """

    def hook(self):
        self.indent = 3

    def heading(self, doc):
        self.rst.directive(name='raw',
                           arg='html',
                           content='<div class="sequence-block"><div class="bullet-block"><div class="sequence-step">{0}</div></div>'.format(doc['stepnum']),
                           indent=0)

        self.rst.newline()


        self.rst.directive('only', 'not latex')

        self.rst.newline()

        self.rst.ref_target('step-{0}-{1}-{2}'.format(doc['stepnum'],
                                                      self.key_name(), doc['ref']),
                                                      indent=3)
        self.rst.newline()

        self._heading(block={ 'heading': doc['title'] },
                      override_char='~',
                      indent=3)

        self.rst.directive(name="class",
                           arg="step-" + str(doc['stepnum']),
                           indent=3)

        self.indent = 6
        self.rst.newline()

    def post_step_hook(self):
        self.rst.directive(name='raw',
                           arg='html',
                           content='</div>'.format(),
                           indent=0)
        self.rst.newline()


def render_step_file(input_fn, output_fn=None):
    steps = Steps(input_fn)
    r = RstCloth()

    web_output = WebStepsOutput(steps)
    web_output.render()
    r.content(web_output.rst.get_block(), indent=0, wrap=False)

    r.directive('only', 'latex')
    r.newline()
    print_output = PrintStepsOutput(steps)
    print_output.render()
    r.content(print_output.rst.get_block(), indent=3, wrap=False)

    if output_fn is None:
        output_fn = os.path.splitext(input_fn)[0] + '.rst'

    r.write(output_fn)
    print('[steps]: rendered step include at ' + output_fn)

if __name__ == '__main__':
    render_step_file(sys.argv[1], sys.argv[2])

"""
Steps schema is:

{
  "title": <str>,
  "ordinal": <int>,
  "pre": <str>,
  "post": <str>,
  "ref": <str>,
  "action": {
               "language": <str>,
               "code": <str>,
               "pre": <str>,
               "post": <str>
             }
}

Notes:
 - ref becomes a global id, but has ``step-<file_name>-`` prepended to it in
   source

 - pre/post are optional

 - Action should be either a doc or a list of docs.

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
"""

import yaml
import sys, os
from rstcloth import RstCloth
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'bin')))
from utils import ingest_yaml_list

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

        idx = 0
        for step in self.source_list:
            if 'source' in step:
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

        self.source_list.sort(key=lambda k:k['ordinal'])

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

    def post(self, doc):
        if 'post' in doc:
            self.rst.content(doc['post'], indent=self.indent)
            self.rst.newline()

    def code_step(self, block):
        self.pre(block)

        self.rst.directive(name='code-block',
                           arg=block['language'],
                           content=block['code'],
                           indent=self.indent)

        self.post(block)

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
        self.rst.ref_target('step-{0}-{1}-{2}'.format(doc['ordinal'],
                                                      self.key_name(),
                                                      doc['ref']))
        self.rst.newline()

        self.rst.h3(text="Step {0}: {1}".format(str(doc['ordinal']),
                    doc['title']),
                    indent=self.indent)
        self.rst.newline()

class WebStepsOutput(StepsOutput):
    """
    Variant of Steps class for generating web-content that depends on CSS
    classes.
    """

    def hook(self):
        self.indent = 3

    def heading(self, doc):
        self.rst.directive(name="class",
                           arg="step-" + str(doc['ordinal']),
                           indent=self.indent-3)

        self.rst.newline()

        self.rst.ref_target('step-{0}-{1}-{2}'.format(doc['ordinal'],
                                                      self.key_name(), doc['ref']),
                                                      indent=self.indent)
        self.rst.newline()
        self.rst.h3(doc['title'], indent=self.indent)
        self.rst.newline()

def render_step_file(input_fn, output_fn=None):
    steps = Steps(input_fn)
    r = RstCloth()

    r.directive('only', 'not latex')
    r.newline()
    web_output = WebStepsOutput(steps)
    web_output.render()
    r.content(web_output.rst.get_block(), indent=3, wrap=False)

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

"""
Steps schema is:

{
  "title": <str>,
  "number": <int>,
  "pre": <str>,
  "post": <str>,
  "ref": <str>,
  "example": {
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

 - Example should be either a doc or a list of docs.

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

    should also include methods for writing the output file.
    """
    def __init__(self, fn, cache=None):
        if cache is None:
            cache = dict()

        self.source_fn = fn
        self.agg_sources = cache
        self.source = ingest_yaml_list(self.source_fn)

        idx = 0
        for step in self.source:
            if 'source' in step:
                source_file = step['source']['file']
                if source_file in self.agg_sources:
                    self.source[idx] = self.agg_sources[source_file]
                    step.pop('number', None)
                    self.source[idx].update(step)
                else:
                    steps = Steps(source_file, self.agg_sources)
                    self.agg_sources[source_file] = steps
                    self.source[idx] = self.agg_sources[source_file]
                    step.pop('number', None)
                    self.source[idx].update(step)
            idx += 1

        self.source.sort(key=lambda k:k['number'])

class StepsOutput(object):
    """
    base class, __init__ method accepts one argument that takes a steps object.

    sub-classes just implement a single render method.
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
        for step in self.steps.source:
            self.heading(step)

            self.pre(step)

            if isinstance(step['example'], list):
                for block in step['example']:
                    self.code_step(block)
            else:
                self.code_step(step['example'])

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
        if 'pre' in block:
            self.rst.content(block['pre'], indent=self.indent)
            self.rst.newline()
        else:
            self.rst.newline()

        self.rst.directive( name='code-block', arg=block['language'], content=block['code'], indent=self.indent)

        if 'post' in block:
            self.rst.content(block['post'], indent=self.indent)
            self.rst.newline()
        else:
            self.rst.newline()

    def key_name(self):
        key_name = os.path.splitext(os.path.basename(self.steps.source_fn))[0]
        if key_name.startswith('step-') or key_name.startswith('steps-'):
            key_name = key_name.split('-', 1)[1]
        
        return key_name
 

class PrintStepsOutput(StepsOutput):
    """
    renders content into rst by creating headlines with "step <num>: " prepended
    to headings
    """
    def hook(self):
        self.indent = 0

    def heading(self, doc):
        self.rst.ref_target('step-{0}-{1}-{2}'.format(doc['number'], self.key_name(), doc['ref']))
        self.rst.newline()

        self.rst.h3(text="Step {0}: {1}".format(str(doc['number']), doc['title']), indent=self.indent)
        self.rst.newline()

class WebStepsOutput(StepsOutput):
    """
    renders content into rst by wrapping objects in rst classes for rst.
    """

    def hook(self):
        self.indent = 3

    def heading(self, doc):
        self.rst.directive(name="class", arg="step-" + str(doc['number']), indent=self.indent-3)
        self.rst.newline()
        self.rst.ref_target('step-{0}-{1}-{2}'.format(doc['number'],
                                                      self.key_name(), doc['ref']), indent=self.indent)
        self.rst.newline()
        self.rst.h3(doc['title'], indent=self.indent)
        self.rst.newline()

def render_step_file(input_fn, output_fn=None):
    if output_fn is None:
        output_fn = os.path.splitext(input_fn)[0] + '.rst'

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

    r.write(output_fn)
    print('[steps]: rendered step include at ' + output_fn)

if __name__ == '__main__':
    render_step_file(sys.argv[1], sys.argv[2])

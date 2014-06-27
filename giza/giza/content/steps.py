import logging
import os.path

logger = logging.getLogger('giza.content.steps')

from giza.files import expand_tree, verbose_remove
from giza.serialization import ingest_yaml_list

from rstcloth.rstcloth import RstCloth

#################### rendering ####################

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
        self.source_dir = os.path.dirname(self.source_fn)
        self.source = dict()

        sort_needed = False

        for idx, step in enumerate(self.source_list):
            if 'stepnum' not in step:
                step['stepnum'] = idx+1
            else:
                sort_needed = True

            if 'source' in step or 'inherit' in step:
                if 'source' in step:
                    source_file = step['source']['file']
                    source_ref = step['source']['ref']
                elif 'inherit' in step:
                    source_file = step['inherit']['file']
                    source_ref = step['inherit']['ref']

                if source_file in self.agg_sources:
                    current_step = self.agg_sources[source_file].get_step(source_ref)
                    msg = 'resolved ref "{0}" from file "{1}" using step cache'
                    logger.debug(msg.format(source_ref, source_file))
                else:
                    msg = 'could *not* resolved ref "{0}" from file "{1}" with step cache'
                    logger.debug(msg.format(source_ref, source_file))
                    if not os.path.exists(fn):
                        msg = 'file {0} does not exist'.format(fn)
                        logger.error(msg)
                        raise InvalidStep(msg)
                    elif fn in self.agg_sources or source_file in self.agg_sources:
                        msg = 'hitting recursion issue on {0}'.format(fn)
                        logger.error(msg)
                        raise InvalidStep(msg)
                    else:
                        msg = "reading and caching step {0} from {1} and caching"
                        logger.debug(msg.format(source_ref, source_file))
                        if source_file == os.path.basename(self.source_fn):
                            current_step = self.get_step(source_ref)
                        else:
                            steps = Steps(os.path.join(self.source_dir, source_file), self.agg_sources)

                            current_step = steps.get_step(source_ref)
                            self.agg_sources[source_file] = steps
                            self.agg_sources.update(steps.agg_sources)

                        logger.debug('successfully cached {0}'.format(source_file))

                if current_step is None:
                    msg = 'Missing ref for {0}:"{1}" in step file "{2}"'.format(source_file, source_ref, os.path.basename(self.source_fn))
                    logger.error(msg)
                    raise InvalidStep(msg)

                current_step.update(step)

                self._validate_step(current_step, ['ref', 'title'])
                self.source[source_ref] = current_step
                self.source_list[idx] = current_step
            else:
                self._validate_step(step, ['ref', 'title'])
                self.source[step['ref']] = step

        if sort_needed is True:
            self.source_list.sort(key=lambda k:k['stepnum'])

    def get_step(self, ref):
        if ref in self.source:
            step = self.source[ref].copy()
            if 'stepnum' in step:
                del step['stepnum']
            return step

    def _validate_step(self, step, keys):
        "cursory checks a step object to make sure it's valid, errors otherwise."

        valid = True
        for i in keys:
            if i not in step or step[i] is None:
                valid = False
                if i == 'ref':
                    logger.error('a step in {0} is missing a ref'.format(self.source_fn))
                else:
                    logger.error('invalid step in {0}, with ref {1}, missing {2}'.format(self.source_fn, step['ref'], i))

        if valid is False:
            raise InvalidStep('invalid steps in {0}'.format(self.source_fn))

class StepsOutput(object):
    """
    Base class for rendered step form. The render() method generates the rst in
    the internal RstCloth object.
    """

    def __init__(self, steps, conf):
        if not isinstance(steps, Steps):
            raise TypeError
        else:
            self.steps = steps

        self.conf = conf
        self.current_step = 1
        self.rst = RstCloth()
        self.hook()

    def hook(self):
        self.indent = 3

    def edition_check(self, step):
        if 'edition' in step:
            if 'edition' in self.conf.project:
                if step['edition'] != self.conf.project.edition:
                    return False
        else:
            return True

    @staticmethod
    def annotate_optional(step):
        if 'optional' in step and step['optional'] is True:
            if isinstance(step['title'], dict):
                step['title']['text'] = 'Optional. ' + step['title']['text']
            else:
                if 'title' in step:
                    step['title'] = 'Optional. ' + step['title']
                elif 'heading' in step:
                    step['heading'] = 'Optional. ' + step['heading']

            del step['optional']
            return step
        else:
            return step

    def render(self):
        for step in self.steps.source_list:
            if self.edition_check(step) is False:
                continue

            step = self.annotate_optional(step)
            self.heading(step)
            self.pre(step)

            self.current_step = step['stepnum']

            if 'action' in step:
                if isinstance(step['action'], list):
                    for block in step['action']:
                        self.code_step(block)
                else:
                    self.code_step(step['action'])

            self.content(step)

            self.post(step)

    def content(self, doc):
        if 'content' in doc and doc['content'] is not None:
            self.rst.content(doc['content'], wrap=False, indent=self.indent)
            self.rst.newline()

    def pre(self, doc):
        if 'pre' in doc and doc['pre'] is not None:
            self.rst.content(doc['pre'], wrap=False, indent=self.indent)
            self.rst.newline()

    def post(self, doc, code_step=False):
        if 'post' in doc and doc['post'] is not None:
            self.rst.content(doc['post'], wrap=False, indent=self.indent)
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

            if block['heading']['text'] is None:
                logger.error('step in "{0}" is missing a heading'.format(os.path.basename(self.steps.source_fn)))
                return

            self.rst.heading(text=block['heading']['text'],
                             char=block['heading']['character'],
                             indent=indent)

            self.rst.newline()

    def code_step(self, block):
        if 'code' in block and 'content' in block:
            raise InvalidStep

        if 'heading' in block:
            self.block_heading(block)

        self.pre(block)

        if 'code' in block:
            if 'language' not in block:
                block['language'] = 'none'

            if not isinstance(block['code'], list):
                block['code'] = block['code'].split('\n')

            self.rst.directive(name='code-block',
                               arg=block['language'],
                               content=block['code'],
                               indent=self.indent)
            self.rst.newline()

        if 'content' in block:
            self.content(block['content'])

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

    def block_heading(self, block):
        self._heading(block, override_char='`', indent=self.indent-3)

    def hook(self):
        self.indent = 0

    def heading(self, doc):
        # self.rst.ref_target('step-{0}-{1}-{2}'.format(doc['stepnum'],
        #                                               self.key_name(),
        #                                               doc['ref']))

        self.rst.newline()

        if isinstance(doc['title'], dict):
            doc['title']['text'] = 'Step {0}: {1}'.format(doc['stepnum'],
                                                          doc['title']['text'])
        else:
            doc['title'] = 'Step {0}: {1}'.format(doc['stepnum'], doc['title'])

        self._heading(block={ 'heading': doc['title'] },
                      override_char='~',
                      indent=self.indent)

class WebStepsOutput(StepsOutput):
    """
    Variant of Steps class for generating web-content that depends on CSS
    classes.
    """

    def hook(self):
        self.indent = 3

    def block_heading(self, block):
        self._heading(block, override_char='`', indent=self.indent)
        self.rst.directive(name="class",
                           arg="step-" + str(self.current_step),
                           indent=3)
        self.rst.newline()

    def heading(self, doc):
        self.rst.directive('only', 'not latex')

        self.rst.newline()

        h_content = ('<div class="sequence-block">' '<div class="bullet-block">'
                     '<div class="sequence-step">' '{0}' '</div>' '</div>')

        self.rst.directive(name='raw',
                           arg='html',
                           content=h_content.format(doc['stepnum']),
                           indent=3)

        self.rst.newline()

        self._heading(block={ 'heading': doc['title'] },
                      override_char='~',
                      indent=3)

        self.indent = 3
        self.rst.newline()

    def post_step_hook(self):
        self.rst.directive(name='raw',
                           arg='html',
                           content='</div>'.format(),
                           indent=3)
        self.rst.newline()

def render_step_file(input_fn, output_fn, conf):
    input_fn_base = os.path.basename(input_fn)
    logger.debug('generating step file for {0}'.format(input_fn_base))
    steps = Steps(input_fn)
    logger.debug('resolved step file input for {0}'.format(input_fn_base))

    r = RstCloth()

    web_output = WebStepsOutput(steps, conf=conf)
    web_output.render()
    r.content(web_output.rst.data, indent=0, wrap=False)
    logger.debug('generated web output for {0}'.format(input_fn_base))

    r.directive('only', 'latex')
    r.newline()
    print_output = PrintStepsOutput(steps, conf=conf)
    print_output.render()
    r.content(print_output.rst.data, indent=3, wrap=False)
    logger.debug('generated print output for {0}'.format(input_fn_base))

    if output_fn is None:
        output_fn = os.path.splitext(input_fn)[0] + '.rst'

    r.write(output_fn)
    logger.debug('wrote step include at {0}'.format(output_fn))

#################### step source iterators ####################

def _get_steps_output_fn(fn, paths):
    root_name = os.path.splitext(os.path.basename(fn).split('-', 1)[1])[0] + '.rst'

    return os.path.join(paths.projectroot, paths.branch_source, 'includes', 'steps', root_name)

def step_sources(paths):
    for fn in expand_tree(os.path.join(paths.projectroot, paths.includes), ' yaml'):
        if fn.startswith(os.path.join(paths.projectroot, paths.includes, 'step')):
            yield fn

def step_outputs(conf):
    for fn in step_sources(conf.paths):
        yield _get_steps_output_fn(fn, conf.paths)

#################### step workers ####################

def steps_tasks(conf, app):
    paths = conf.paths

    for fn in expand_tree(os.path.join(paths.projectroot, paths.includes), 'yaml'):
        if fn.startswith(os.path.join(paths.projectroot, paths.includes, 'step')):
            out_fn = _get_steps_output_fn(fn, paths)

            task = app.add('task')
            task.dependency = fn
            task.target = out_fn
            task.job = render_step_file
            task.args = [fn, out_fn, conf]
            logger.debug('added task to generate step: {0}'.format(out_fn))

def steps_clean(conf, app):
    for fn in step_outputs(conf):
        task = app.add('task')
        task.job = verbose_remove
        task.args = [fn]
        task.description = 'removing {0}'.format(fn)

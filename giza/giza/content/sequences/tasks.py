import os
import logging

logger = logging.getLogger('giza.content.steps.tasks')

from giza.tools.files import expand_tree
from giza.content.sequences.inheritance import StepDataCache
from giza.content.sequences.views import render_steps

def write_steps(steps, fn, conf):
    content = render_steps(steps, conf)
    content.write(fn)
    logger.debug('wrote steps to: '  + fn)

def step_task_maker(conf, app):
    include_dir = os.path.join(conf.paths.projectroot, conf.paths.includes)
    fn_prefix = os.path.join(include_dir, 'steps')

    step_sources = [ fn for fn in
                     expand_tree(include_dir, 'yaml')
                     if fn.startswith(fn_prefix) ]

    s = StepDataCache(step_sources, conf)

    if not os.path.isdir(fn_prefix):
        os.makedirs(fn_prefix)

    for fn in s.cache.keys():
        stepf = s.cache[fn]

        basename = fn[len(fn_prefix)+1:-5]

        out_fn = os.path.join(conf.paths.projectroot,
                              conf.paths.branch_source,
                              'includes', 'steps', basename) + '.rst'

        t = app.add('task')
        t.target = out_fn
        t.dependency = fn
        t.job = write_steps
        t.args = (stepf, out_fn, conf)
        t.description = 'generate an stepfile for ' + fn

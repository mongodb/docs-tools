import os

from giza.tools.files import expand_tree
from giza.content.sequences.inheritance import StepDataCache

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

        print(' '.join(['steps ->', out_fn]))

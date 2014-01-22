import os.path

try:
    from utils.files import expand_tree
    from utils.rstcloth.steps import render_step_file
except ImportError:
    from ..files import expand_tree
    from ..rstcloth.steps import render_step_file

#################### steps ####################

def _get_steps_output_fn(fn, paths):
    root_name = os.path.splitext(os.path.basename(fn).split('-', 1)[1])[0] + '.rst'

    return os.path.join(paths.projectroot, paths.includes, 'steps', root_name)

def steps_jobs(conf):
    paths = conf.paths

    for fn in expand_tree(os.path.join(paths.projectroot, paths.includes), 'yaml'):
        if fn.startswith(os.path.join(paths.projectroot, paths.includes, 'step')):
            out_fn = _get_steps_output_fn(fn, paths)

            yield { 'dependency': fn,
                    'target': out_fn,
                    'job': render_step_file,
                    'args': [fn, out_fn] }

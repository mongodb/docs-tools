import os

from utils.files import expand_tree

from rstcloth.options import Options, OptionRendered

def render_option_page(opt, path):
    renderer = OptionRendered(opt)
    renderer.render(path)

def option_jobs(conf):
    paths = conf.paths

    options = Options()

    base_path = os.path.join(paths.projectroot, paths.includes)
    output_path = os.path.join(base_path, 'option')

    for fn in expand_tree(base_path, 'yaml'):
        if fn.startswith(output_path):
            options.ingest(fn)

    if not os.path.exists(output_path):
        os.makedirs(output_path)

    for opt in options.iterator():
        yield { 'job': render_option_page,
                'args': [ opt, output_path ]
              }

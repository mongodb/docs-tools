import os.path
import sys
import imp

from utils.config import lazy_conf
from utils.files import expand_tree

def external_jobs(conf=None):
    conf = lazy_conf(conf)

    ext_mod_path = os.path.join(conf.paths.projectroot, 'local')
    if not os.path.exists(ext_mod_path):
        raise StopIteration

    external_mods = []

    for mod in expand_tree(ext_mod_path, 'py'):
        path, name = os.path.split(mod)
        name, _ = os.path.splitext(name)

        file, filename, data = imp.find_module(name, [path])

        imp.load_module(name, file, mod, data)
        external_mods.append(name)

    for name in external_mods:
        mod = sys.modules[name]
        if 'jobs' in dir(mod) and 'stage' in dir(mod) and mod.stage.startswith('pre'):
            for task in mod.jobs(conf):
                yield task

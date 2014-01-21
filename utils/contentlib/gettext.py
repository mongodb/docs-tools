import os.path

from utils.config import lazy_conf
from utils.files import expand_tree, copy_if_needed

#################### Gettext Processing ####################

def gettext_jobs(conf=None):
    conf = lazy_conf(conf)

    locale_dirs = os.path.join(conf.paths.projectroot,
                               conf.paths.locale, 'pot')

    branch_output = os.path.join(conf.paths.projectroot,
                                       conf.paths.branch_output,
                                       'gettext')

    path_offset = len(branch_output) + 1

    for fn in expand_tree(branch_output, None):
        yield {
            'job': copy_if_needed,
            'args': [ fn, os.path.join(locale_dirs, fn[path_offset:]), None]
        }

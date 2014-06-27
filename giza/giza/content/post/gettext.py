import os.path

from giza.files import expand_tree, copy_if_needed

#################### Gettext Processing ####################

def gettext_tasks(conf, app):
    locale_dirs = os.path.join(conf.paths.projectroot,
                               conf.paths.locale, 'pot')

    branch_output = os.path.join(conf.paths.projectroot,
                                       conf.paths.branch_output,
                                       'gettext')

    path_offset = len(branch_output) + 1

    for fn in expand_tree(branch_output, None):
        task = app.add('task')
        task.target = fn
        task.job = copy_if_needed
        task.args = [ fn, os.path.join(locale_dirs, fn[path_offset:]), None]
        task.description = "migrating po file {0} if needed".format(fn)

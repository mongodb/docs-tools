from fabric.api import lcd, local, task

from docs_meta import conf

@task
def make(target):
    with lcd(conf.build.paths.projectroot):
        if isinstance(target, list):
            target_str = make + ' '.join([target])
        elif isinstance(target, basestring):
            target_str = ' '.join(['make', target])

        local(target_str)

import os
from fabric.api import lcd, local, task
from docs_meta import get_conf

@task
def make(target):
    with lcd(get_conf().build.paths.projectroot):
        if isinstance(target, list):
            target_str = make + ' '.join([target])
        elif isinstance(target, basestring):
            target_str = ' '.join(['make', target])

        local(target_str)

def check_three_way_dependency(target, source, dependency):
    if not os.path.exists(target):
        # if .json doesn't exist, rebuild
        return True
    else:
        dep_mtime = os.stat(dependency).st_mtime
        if os.stat(source).st_mtime > dep_mtime:
            # if <file>.txt is older than <file>.fjson,
            return True
        elif dep_mtime > os.stat(target).st_mtime:
            #if fjson is older than json
            return True
        else:
            return False

def check_list_dependency(target, dependencies):
    if not os.path.exists(target):
        return True
    else:
        needs_rebuild = False

        target_time = os.stat(target).st_mtime
        for dep in dependencies:
            if target_time < os.stat(dep).st_mtime:
                needs_rebuild = True
                break

        return needs_rebuild

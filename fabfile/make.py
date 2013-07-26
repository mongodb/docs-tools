import os
from fabric.api import lcd, local, task, env
from docs_meta import get_conf

env.FORCE = False
@task
def force():
    env.FORCE = True

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

def check_multi_dependency(target, dependency, pass_non_existing=True):
    for t in target:
        if check_dependency(t, dependency, pass_non_existing) is True:
            print "---" + t + "---"
            return True

    return False

def check_dependency(target, dependency, pass_non_existing=False):
    if not os.path.exists(target):
        if pass_non_existing is False:
            if not os.path.islink(target):
                return True
        else:
            return False

    def needs_rebuild(targ_t, dep_f):
        if targ_t < os.stat(dep_f).st_mtime:
            return True
        else:
            return False

    target_time = os.stat(target).st_mtime
    if isinstance(dependency, list):
        ret = False
        for dep in dependency:
            if needs_rebuild(target_time, dep):
                ret = True
                break
        return ret
    else:
        return needs_rebuild(target_time, dependency)

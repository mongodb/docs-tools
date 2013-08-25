from make import _make as make
from docs_meta import get_conf

def manpage_jobs():
    conf = get_conf()
    if conf.project.name != 'mongodb-manual':
        return
    elif conf.git.branches.current == 'v2.2':
        return
    else:
        yield dict(dependency=None, target='generate-manpages', job=make, args=['generate-manpages'])

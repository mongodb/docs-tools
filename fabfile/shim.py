from make import _make as make
from docs_meta import load_conf

def manpage_jobs():
    if load_conf().project.name == 'mms':
        return
    else:
        yield dict(dependency=None, target='generate-manpages', job=make, args=['generate-manpages'])
    

from make import _make as make

def manpage_jobs():
    yield dict(dependency=None, target='generate-manpages', job=make, args=['generate-manpages'])
    

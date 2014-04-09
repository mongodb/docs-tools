import os.path
import logging
import re

from fabric.api import task, env, abort

from fabfile.utils.transformations import munge_page
from fabfile.utils.files import expand_tree
from fabfile.utils.config import lazy_conf
from fabfile.utils.jobs.context_pools import ProcessPool

logger = logging.getLogger(os.path.basename(__file__))

env.regex = None
env.replacement = None

@task
def regex(st): 
    env.regex = re.compile(r'(:setting:`){0}(`)'.format(st))

@task
def replace(st):
    env.replacement = r'\1{0}\2'.format(st)

@task
def test():
    print('regex: ' + str(env.regex.pattern))
    print('replaccement: ' + str(env.replacement))

@task
def batch():
    queue = [
    # ( regex, replace), 
      ('sslCAFile', '~net.ssl.CAFile'),
      ('sslFIPSMode', '~net.ssl.FIPSMode'),
      ('sslClusterFile', '~net.ssl.ClusterFile'),
      ('sslPEMKeyFile', '~net.ssl.PEMKeyfile'),
      ('sslPEMKeyPassword', '~net.ssl.PEMKeyPassword'),
      ('sslClusterPassword', '~net.ssl.ClusterPassword'),
      ('sslCRLKeyFile', '~net.ssl.CRLKeyfile'),
    ]

    for regst, replst in queue:
        regex(regst)
        replace(replst)
        test()
        run()
        

@task
def run():
    if env.regex is None:
        abort('must specify a regex')
    if env.replacement is None:
        abort('must specify a replacement')

    conf = lazy_conf()

    source_dir = os.path.join(conf.paths.projectroot, conf.paths.source)

    files = expand_tree(path=source_dir, input_extension=None)
    
    results = []
    with ProcessPool() as p:
        for fn in files:
            r = p.apply_async(munge_page, args=[fn, (env.regex, env.replacement), fn, 'editing' ])
            results.append(r)
            
    # results = [ r.get() for r in results ]

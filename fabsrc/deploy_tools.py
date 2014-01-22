from urllib2 import urlopen
from fabric.api import env, task

from fabfile.utils.git import get_commit, get_branch
from fabfile.utils.config import lazy_conf

# this isn't used or wired in at the moment. Pulled out of deploy.py

class PublicationError(Exception): pass

@task
def check(site, conf=None):
    conf = lazy_conf(conf)

    if site.startswith('stag'):
        env.release_info_url = 'http://test.docs.10gen.cc/{0}/release.txt'.format(str(get_branch()))
    elif site == 'ecosystem':
        env.release_info_url = 'http://docs.mongodb.org/ecosystem/release.txt'
    elif site.startswith('prod') or site.startswith('pub'):
        env.release_info_url = 'http://docs.mongodb.org/{0}/release.txt'.format(conf.git.branches.current)

    r = urlopen(env.release_info_url).readlines()[0].split('\n')[0]
    if get_commit() == r:
        raise PublicationError('ERROR: the current published version of is the same as the current commit. Make a new commit before publishing.')
    else:
        print('[build]: the current commit is different than the published version on.')

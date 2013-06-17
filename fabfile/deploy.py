from fabric.api import cd, local, task, abort, env, puts
from fabric.utils import _AttributeDict as ad

import utils 
import os.path
from docs_meta import conf, render_paths, get_branch, get_commit
from urllib2 import urlopen

_pub_hosts = ['www@www-c1.10gen.cc', 'www@www-c2.10gen.cc']

env.paths = render_paths('dict')
try:
    env.push_conf = utils.ingest_yaml(os.path.join(conf.build.paths.builddata, 'push.yaml'))
except IOError:
    puts('[deploy]: push.yaml file does not exist. not throwing exception.')

def validate_branch(branch):
    if env.push_conf['project'] != 'manual' and env.project == 'stage': 
        pass
    else: 
        if branch == 'override':
            pass
        elif branch is None:
            abort('must specify a branch')
        elif branch not in conf.git.branches.published:
            abort('must specify a published branch.')

@task
def staging(branch=None):
    env.project = 'stage'

    validate_branch(branch, env='stage')

    env.hosts = ['public@test.docs.10gen.cc']
    env.remote_rsync_location = '/srv/public/test/' + str(branch)
    env.release_info_url = 'http://test.docs.10gen.cc/{0}/release.txt'.format(str(branch))

@task
def production(branch=None):
    env.project = 'production'
    validate_branch(branch)

    env.hosts = _pub_hosts
    env.remote_rsync_location = '/data/sites/docs/' + str(branch)
    env.release_info_url = 'http://docs.mongodb.org/{0}/release.txt'.format(str(branch))

@task
def mms(version='saas'):
    env.project = 'mms'
    env.hosts = _pub_hosts
    
    if conf.git.remote != '10gen/mms-docs':
        abort('this is not the mms docs repo, refusing to deploy.')

    env.mms_version = version

    if version == 'saas': 
        env.remote_rsync_location = '/data/sites/docs/mms'
    elif version == 'hosted':
        env.remote_rsync_location = '/data/sites/docs/mms-hosted'

@task
def ecosystem():
    env.project = 'ecosystem'

    if conf.git.remote != 'mongodb/docs-ecosystem':
        abort('this is not the ecosystem docs repo, refusing to deploy.')

    env.hosts = _pub_hosts
    env.remote_rsync_location = '/data/sites/docs/ecosystem'
    env.release_info_url = 'http://docs.mongodb.org/ecosystem/release.txt'

@task
def about():
    env.project = 'about'

    if conf.git.remote != '10gen/mongodb-www-about':
        abort('this is not the about repo, refusing to deploy.')

    env.hosts = _pub_hosts
    env.remote_rsync_location = '/data/sites/mongodborg-static'

def build_rsync_cmd(local_path, remote_string, recursive=True, delete=None):
    return [
        'rsync',
        '-ltz' if delete != 'delete' else '-ltz --delete',
        '-qcr' if recursive is True else '-cq',
        local_path,
        remote_string
        ]

@task
def check():
    r = urlopen(env.release_info_url).readlines()[0].split('\n')[0]

    if get_commit() == r:
        abort('ERROR: the current published version of is the same as the current commit. Make a new commit before publishing.')
    else:
        puts('[build]: the current commit is different than the published version on. Building now.')

@task
def push(delete=None):
    if not env.hosts:
        abort('must specify a deployment mode: staging or production')

    cmd = []
    if env.project == 'mms':
        cmd.append(build_rsync_cmd(local_path=os.path.join(env.paths['branch-staging'], env.mms_version) + os.path.sep,
                          remote_string=env.host_string + ':' + env.remote_rsync_location,
                          delete=delete))
        cmd.append([ 'rsync', 
                     os.path.join(env.paths['branch-staging'], env.mms_version, '.htaccess'), 
                     env.host_string + ':' + os.path.join(env.remote_rsync_location, '.htaccess'),
                    ])
    else:
        cmd.append(build_rsync_cmd(local_path=env.paths['branch-staging'] + os.path.sep,
                          remote_string=env.host_string + ':' + env.remote_rsync_location,
                          delete=delete))

    for c in cmd:
        local(' '.join(c))

@task
def everything(override=None):
    if env.project == 'mms':
        abort('[deploy]: the mms project has an atypical deployment')

    if override != 'override':
        abort('must specify override to deploy everything')

    cmd = build_rsync_cmd(local_path=env.paths['public'] + os.path.sep,
                          remote_string=env.host_string + ':' + env.remote_rsync_location.rsplit('/', 1)[0])

    local(' '.join(cmd))

@task
def static():
    if env.project == 'mms':
        abort('[deploy]: the mms project has an atypical deployment')

    if get_branch() == conf.git.branches.manual:
        cmd = [ build_rsync_cmd(local_path=env.paths['public'] + '/*',
                               remote_string=env.host_string + ':' + env.remote_rsync_location.rsplit('/', 1)[0],
                               recursive=False),
               build_rsync_cmd(local_path=env.paths['public'] + '/.htaccess',
                               remote_string=env.host_string + ':' + env.remote_rsync_location.rsplit('/', 1)[0],
                               recursive=False) ]

        for c in cmd:
            local(' '.join(c))

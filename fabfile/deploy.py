from fabric.api import cd, local, task, abort, env, puts, parallel
from fabric.utils import _AttributeDict as ad

import os.path
from docs_meta import get_conf, render_paths, get_branch, get_commit
from urllib2 import urlopen

_pub_hosts = ['www-c1.10gen.cc', 'www-c2.10gen.cc']
_stage_hosts = ['public@test.docs.10gen.cc']
env.rsync_options = ad()
env.rsync_options.default = '-cqltz'
env.rsync_options.recursive = None
env.rsync_options.delete = None
env.paths = render_paths('dict')

def validate_branch(branch):
    if branch == 'override':
        pass
    elif branch is None:
        abort('must specify a branch')
    elif branch not in get_conf().git.branches.published:
        abort('must specify a published branch.')

def rsync_options(recursive, delete):
    r = [env.rsync_options.default]

    if recursive is True:
        r.append('--recursive')

    if delete is True:
        r.append('--delete')

    if env.deploy_target == 'production':
        r.extend(['--rsh="ssh"', '--rsync-path="sudo -u www rsync"'])

    return ' '.join(r)

########## Tasks -- Checking current build against production. ############

@task
def staging(branch=None):
    env.release_info_url = 'http://test.docs.10gen.cc/{0}/release.txt'.format(str(branch))

@task(alias='production')
def publication(branch=None):
    validate_branch(branch)
    env.release_info_url = 'http://docs.mongodb.org/{0}/release.txt'.format(str(branch))

@task
def ecosystem():
    env.release_info_url = 'http://docs.mongodb.org/ecosystem/release.txt'

@task
@parallel
def check():
    r = urlopen(env.release_info_url).readlines()[0].split('\n')[0]
    if get_commit() == r:
        abort('ERROR: the current published version of is the same as the current commit. Make a new commit before publishing.')
    else:
        puts('[build]: the current commit is different than the published version on. Building now.')

########## Tasks -- Deployment and configuration. ############

@task
def remote(host):
    if host in ['publication', 'mms']:
        env.hosts = _pub_hosts
        env.deploy_target = 'production'
    elif host.startswith('stag'): # staging or stage
        env.deploy_target = 'staging'
        env.hosts = _stage_hosts
    else:
        abort('[deploy]: must specify a valid host to deploy the docs to.')

@task
def recursive(opt=True):
    env.rsync_options.recursive = opt

@task
def delete(opt=True):
    env.rsync_options.delete = opt


@task
@parallel
def static(local_path='all', remote=None):
    if local_path.endswith('.htaccess') and env.branch != 'master':
        puts('[deploy] [ERROR]: cowardly refusing to deploy a non-master htaccess file.')
        return False

    cmd = [ 'rsync', rsync_options(recursive=False, delete=False) ]

    if local_path == 'all':
        local_path = '*'

    cmd.append(local_path)

    cmd.append(':'.join([env.host_string, remote]))

    puts('[deploy]: migrating {0} files to {1} remote'.format(local_path, remote))
    local(' '.join(cmd))
    puts('[deploy]: completed migration of {0} files to {1} remote'.format(local_path, remote))

@task
@parallel
def push(local_path, remote):
    if get_conf().project.name == 'mms' and (env.branch != 'master' and
                                             env.edition == 'saas'):
        puts('[deploy] [ERROR]: cowardly refusing to push non-master saas.')
        return False

    if local_path.endswith('/') or local_path.endswith('/*'):
        local_path = local_path
    else:
        local_path = local_path + '/'

    if remote.endswith('/'):
        remote = remote[:-1]
    else:
        remote = remote

    cmd = [ 'rsync',
            rsync_options(env.rsync_options.recursive,
                          env.rsync_options.delete),
            local_path,
            ':'.join([env.host_string, remote]) ]

    puts('[deploy]: migrating {0} files to {1} remote'.format(local_path, remote))
    local(' '.join(cmd))
    puts('[deploy]: completed migration of {0} files to {1} remote'.format(local_path, remote))

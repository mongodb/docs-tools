import os.path
from urllib2 import urlopen

from fabric.api import cd, local, task, abort, env, puts, parallel
from fabric.utils import _AttributeDict as ad
from sphinx import edition_setup

from docs_meta import get_conf, render_paths, get_branch, get_commit
from utils import ingest_yaml_list, conf_from_list
from make import runner

_pub_hosts = ['www-c1.10gen.cc', 'www-c2.10gen.cc']
_stage_hosts = ['public@test.docs.10gen.cc']

env.rsync_options = ad()
env.rsync_options.default = '-cqltz'
env.rsync_options.recursive = None
env.rsync_options.delete = None
env.paths = render_paths('dict')

def rsync_options(recursive, delete, environ):
    r = [env.rsync_options.default]

    if recursive is True:
        r.append('--recursive')

    if delete is True:
        r.append('--delete')

    if environ == 'production':
        r.extend(['--rsh="ssh"', '--rsync-path="sudo -u www rsync"'])

    return ' '.join(r)

########## Tasks -- Checking current build against production. ############

@task
def check(site, conf=None):
    if conf is None:
        conf = get_conf()
    if site.startswith('stag'):
        env.release_info_url = 'http://test.docs.10gen.cc/{0}/release.txt'.format(str(branch))
    elif site == 'ecosystem':
        env.release_info_url = 'http://docs.mongodb.org/ecosystem/release.txt'
    elif site.startswith('prod') or site.startswith('pub'):
        env.release_info_url = 'http://docs.mongodb.org/{0}/release.txt'.format(conf.git.branches.current)

    r = urlopen(env.release_info_url).readlines()[0].split('\n')[0]
    if get_commit() == r:
        abort('ERROR: the current published version of is the same as the current commit. Make a new commit before publishing.')
    else:
        puts('[build]: the current commit is different than the published version on.')

########## Tasks -- Deployment and configuration. ############

def static_worker(local_path, remote, host_string, recursive, delete, environ, pconf, conf):

    if local_path.endswith('.htaccess') and conf.git.branches.current != 'master':
        puts('[deploy] [ERROR]: cowardly refusing to deploy a non-master htaccess file.')
        return False

    cmd = [ 'rsync', rsync_options(recursive=recursive, delete=delete, environ=environ) ]

    cmd.append(local_path)

    cmd.append(':'.join([host_string, remote]))

    puts('[deploy]: migrating {0} files to {1} remote'.format(local_path, remote))
    local(' '.join(cmd))
    puts('[deploy]: completed migration of {0} files to {1} remote'.format(local_path, remote))

def push_worker(local_path, remote, host_string, recursive, delete, environ, pconf, conf):
    if get_conf().project.name == 'mms' and (conf.git.branches.current != 'master' and
                                             pconf.edition == 'saas'):
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
            rsync_options(recursive, delete, environ),
            local_path,
            ':'.join([host_string, remote]) ]

    puts('[deploy]: migrating {0} files to {1} remote'.format(local_path, remote))
    local(' '.join(cmd))
    puts('[deploy]: completed migration of {0} files to {1} remote'.format(local_path, remote))

############################## Deploy -- Generic Deployment Framework ##############################

def get_branched_path(options, conf=None, *args):
    if conf is None:
        conf = get_conf()

    if 'branched' in options:
        return os.path.join(os.path.sep.join(args),
                            conf.git.branches.current)
    else:
        return os.path.sep.join(args)

@task
def deploy(target, conf=None, pconf=None):
    """Deploys a site. Specifies the deployment target defined in 'push.yaml'"""

    if conf is None:
        conf = get_conf()

    push_conf = ingest_yaml_list(os.path.join(conf.build.paths.projectroot,
                                              conf.build.paths.builddata,
                                              'push.yaml'))

    pconf = conf_from_list('target', push_conf)[target]


    if pconf['target'] != target:
        abort('[deploy] [ERROR]: this build environment does not support the {0} target'.format(target))

    count = runner(deploy_jobs(target, conf, pconf), pool=2)
    puts('[deploy]: pushed {0} targets'.format(count))

def deploy_jobs(target, conf, pconf):
    if 'edition' in pconf:
        conf = edition_setup(pconf.edition, conf)

    if 'recursive' in pconf.options:
        env.rsync_options.recursive = True
    if 'delete' in pconf.options:
        env.rsync_options.delete = True

    if pconf.env in ['publication', 'mms']:
        hosts = _pub_hosts
        deploy_target = 'production'
    elif pconf.env.startswith('stag'): # staging or stage
        deploy_target = 'staging'
        hosts = _stage_hosts
    else:
        abort('[deploy]: must specify a valid host to deploy the docs to.')


    args = dict(local_path=get_branched_path(pconf.options, conf, conf.build.paths.output, pconf.paths.local),
                remote=get_branched_path(pconf.options, conf, pconf.paths.remote),
                host_string=None,
                recursive=env.rsync_options.recursive,
                delete=env.rsync_options.delete,
                environ=deploy_target,
                pconf=pconf,
                conf=conf)

    for host in hosts:
        args['host_string'] = host
        yield { 'job': static_worker if 'static' in pconf.options else push_worker,
                'args': args.copy(),
                'target': None,
                'dependency': None }

    try:
        if isinstance(pconf.paths.static, list):
            for static_path in pconf.paths.static:
                for job in static_deploy(args, static_path, hosts, conf, pconf):
                    yield job
        else:
            for job in static_deploy(args, pconf.paths.static, hosts, conf, pconf):
                yield job
    except AttributeError:
        puts('[deploy] [ERROR]: not deploying any static content')

def static_deploy(args, static_path, hosts, conf, pconf):
    if static_path in ['manual', 'current']:
        args['remote'] = pconf.paths.remote
    else:
        args['remote'] = os.path.join(pconf.paths.remote, static_path)

    args['local_path'] = os.path.join(conf.build.paths.output, pconf.paths.local, static_path)


    for host in hosts:
        args['host_string'] = host
        yield { 'job': static_worker,
                'args': args.copy(),
                'target': None,
                'dependency': None }

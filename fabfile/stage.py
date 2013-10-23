import os
import datetime
import tarfile
import urllib2

from fabric.api import task, puts, abort, env
from docs_meta import get_conf
from utils import conf_from_list, ingest_yaml_list

from deploy import deploy as production_deploy

@task
def package(conf=None):
    if conf is None:
        conf = get_conf()

    archive_path = os.path.join(conf.build.paths.projectroot, conf.build.paths.buildarchive)

    fn = os.path.join(archive_path, '-'.join([conf.project.name,
                                              conf.git.branches.current,
                                              conf.git.commit[:8],
                                              datetime.datetime.utcnow().strftime('%s') ]) + '.tar.gz')

    pconf = conf_from_list('target', ingest_yaml_list(os.path.join(conf.build.paths.projectroot,
                                                                   conf.build.paths.builddata,
                                                                   'push.yaml')))['push']

    if not os.path.exists(archive_path):
        os.makedirs(archive_path)
        puts('[deploy] [tarball]: creating {0} directory'.format(archive_path))
    else:
        if not os.path.isdir(archive_path):
            abort('[ERROR]: {0} exists and is not a directory.'.format(archive_path))

    with tarfile.open(fn, 'w:gz') as t:
        t.add(name=os.path.join(conf.build.paths.projectroot, conf.build.paths.public_site_output),
              arcname=conf.git.branches.current)

        if 'static' in pconf.paths:
            for path in pconf.paths.static:
                t.add(name=os.path.join(conf.build.paths.projectroot,
                                        conf.build.paths.public,
                                        path),
                      arcname=path)
    puts('[deploy] [tarball]: created {0} as archive of current build artifacts.'.format(fn))

@task
def fetch(path, conf=None):
    if conf is None:
        conf = get_conf()

    local_path = path.split('/')[-1]

    tar_path = os.path.join(conf.build.paths.projectroot,
                            conf.build.paths.buildarchive,
                            local_path)

    if not os.path.exists(tar_path):
        u = urllib2.urlopen(path)
        with open(tar_path, 'w') as f:
            f.write(u.read())
        puts('[deploy] [tarball]: downloaded {0}'.format(local_path))
    else:
        puts('[deploy] [tarball]: {0} exists locally, not downloading.'.format(local_path))

@task
def unwind(path, conf=None):
    if conf is None:
        conf = get_conf()

    if path.startswith('http'):
        tar_path = fetch(path, conf)
    else:
        tar_path = path

    with tarfile.open(tar_path, "r:gz") as t:
        t.extractall(os.path.join(conf.build.paths.projectroot, conf.build.paths.public))

    puts('[deploy] [tarball]: extracted {0} archive into {1}.'.format(tar_path, conf.build.paths.public))
    return tar_path

env.deploy_target = None
@task
def target(target):
    env.deploy_target = target

@task
def deploy(path):
    if conf is None:
        conf = get_conf()

    tar_path = unwind(path, conf)

    if not tar_path.split('/')[-1].startswith('-'.join([conf.project.name, conf.git.branches.current])):
        abort('[deploy] [tarball] [ERROR]: cannot deploy branches other than: {0}'.format(conf.git.branches.current))

    # production_deploy(env.deploy_target)
    puts("[deploy] [tarball]: If this were reality, we would have deployed. here. But it's not. So we didn't. Run 'fab deploy.deploy:{0}' to deploy staged content.".format(env.deploy_target))

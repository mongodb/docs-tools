import os
import sys
import datetime
import tarfile
import urllib2
import json

import yaml
from fabric.api import task, puts, abort, env
from docs_meta import get_conf
from utils import conf_from_list, ingest_yaml_list, write_yaml, BuildConfiguration

from deploy import deploy as production_deploy

def get_build_metadata(conf=None):
    if conf is None:
        conf=get_conf()

    o = dict(push=dict(), conf=conf, meta=dict())

    for target in ingest_yaml_list(os.path.join(conf.build.paths.projectroot,
                                                conf.build.paths.builddata,
                                                'push.yaml')):
        o['push'][target['target']] = target

    o['meta']['user'] = os.getlogin()
    o['meta']['platform'] = sys.platform
    o['meta']['time'] = utc=datetime.datetime.utcnow().isoformat()
    o['meta']['host'] = os.uname()[1]
    return o

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

    arc_conf = os.path.join(conf.build.paths.projectroot,
                            conf.build.paths.branch_output,
                            'conf.json')

    with open(arc_conf, 'w') as f:
        json.dump(get_build_metadata(conf), f, indent=2)

    with tarfile.open(fn, 'w:gz') as t:
        t.add(name=os.path.join(conf.build.paths.projectroot, conf.build.paths.public_site_output),
              arcname=conf.git.branches.current)
        t.add(arc_conf, arcname='conf.json')

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

    arc_file = os.path.join(conf.build.paths.projectroot,
                            conf.build.paths.public,
                            'conf.json')

    new_conf = BuildConfiguration(arc_file)

    new_conf.conf.build.paths.projectroot = conf.build.paths.projectroot

    os.remove(arc_file)

    puts('[deploy] [tarball]: extracted {0} archive into {1}.'.format(tar_path, conf.build.paths.public))
    return tar_path, new_conf

env.deploy_target = None
@task
def target(target):
    env.deploy_target = target

@task
def deploy(path, conf=None):
    if conf is None:
        conf = get_conf()

    tar_path, meta_conf = unwind(path, conf)

    pconf = meta_conf.push
    conf = meta_conf.conf

    if not tar_path.split('/')[-1].startswith('-'.join([conf.project.name, conf.git.branches.current])):
        abort('[deploy] [tarball] [ERROR]: cannot deploy branches other than: {0}'.format(conf.git.branches.current))

    # production_deploy(env.deploy_target, conf, pconf)
    puts("[deploy] [tarball]: If this were reality, we would have deployed. here. But it's not. So we didn't. Run 'fab deploy.deploy:{0}' to deploy staged content.".format(env.deploy_target))

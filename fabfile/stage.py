import os
import datetime
import tarfile
from fabric.api import task, puts
from docs_meta import get_conf
from utils import conf_from_list, ingest_yaml_list

@task
def make_deploy_tarball(conf=None):
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
def tarball_unwind(path, conf=None):
    if conf is None:
        conf = get_conf()

    with tarfile.open(path, "r:gz") as t:
        t.extractall(os.path.join(conf.build.paths.projectroot, conf.build.paths.public))

    puts('[deploy] [tarball]: extracted {0} archive into {1}.'.format(path, conf.build.paths.public))

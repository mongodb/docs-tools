import os.path

from utils.config import lazy_conf
from utils.serialization import ingest_yaml

from utils.contentlib.rstcloth.releases import (generate_release_output,
                                                generate_release_copy,
                                                generate_release_untar)

#################### Snippets for Inclusion in Installation Guides  ####################

# generate_release_output(builder, platform, version, release)

def _generate_release_ent(rel, target, release):
    r = generate_release_output( rel['type'], rel['type'].split('-')[0], rel['system'], release )
    r.write(target)
    print('[release]: wrote: ' + target)

def _generate_release_core(rel, target, release):
    r = generate_release_output( rel, rel.split('-')[0], 'core', release )
    r.write(target)
    print('[release]: wrote: ' + target)

def _generate_untar_core(rel, target, release):
    r = generate_release_untar(rel, release)
    r.write(target)
    print('[release]: wrote: ' + target)

def _generate_copy_core(rel, target, release):
    r = generate_release_copy(rel, release)
    r.write(target)
    print('[release]: wrote: ' + target)

def release_jobs(conf=None):
    conf = lazy_conf(conf)

    data_file = os.path.join(conf.paths.builddata, 'releases') + '.yaml'

    if 'release' in conf.version:
        release_version = conf.version.release
    else:
        release_version = conf.version.published[0]

    if not os.path.exists(data_file):
        return

    rel_data = ingest_yaml(os.path.join(conf.paths.builddata, 'releases') + '.yaml')

    deps = [ os.path.join(conf.system.conf_file),
             os.path.join(conf.paths.projectroot,
                          conf.paths.buildsystem,
                          'rstcloth', 'releases.py'),
           ]

    for rel in rel_data['source-files']:
        target = os.path.join(conf.paths.projectroot,
                              conf.paths.includes,
                              'install-curl-release-{0}.rst'.format(rel))

        yield {
                'target': target,
                'dependency': deps,
                'job': _generate_release_core,
                'args': [ rel, target, release_version ]
              }

        target = os.path.join(conf.paths.projectroot,
                              conf.paths.includes,
                              'install-untar-release-{0}.rst'.format(rel))
        yield {
                'target': target,
                'dependency': deps,
                'job': _generate_untar_core,
                'args': [ rel, target, release_version ]
              }

        target = os.path.join(conf.paths.projectroot,
                              conf.paths.includes,
                              'install-copy-release-{0}.rst'.format(rel))
        yield {
                'target': target,
                'dependency': deps,
                'job': _generate_copy_core,
                'args': [ rel, target, release_version ]
              }

    for rel in rel_data['subscription-build']:
        target = 'source/includes/install-curl-release-ent-{0}.rst'.format(rel['system'])

        yield {
                'target': target,
                'dependency': deps,
                'job': _generate_release_ent,
                'args': [ rel, target, release_version ]
              }

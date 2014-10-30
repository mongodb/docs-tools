# Copyright 2014 MongoDB, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import os.path

logger = logging.getLogger('giza.content.release')

from giza.tools.serialization import ingest_yaml
from rstcloth.rstcloth import RstCloth

def generate_output(builder, platform, version, release):
    """ This is the legacy version of the function used by the makefile and CLI infrastructure"""

    r = RstCloth()

    r.directive('code-block', 'sh', block='header')
    r.newline(block='header')

    if release == 'core':
        r.content('curl -O http://downloads.mongodb.org/{0}/mongodb-{1}-{2}.tgz'.format(platform, builder, version), 3, wrap=False, block='cmd')
    else:
        r.content('curl -O http://downloads.10gen.com/linux/mongodb-{0}-enterprise-{1}-{2}.tgz'.format(builder, release, version), 3, wrap=False, block='cmd')
        r.content('tar -zxvf mongodb-{0}-enterprise-{1}-{2}.tgz'.format(builder, release, version), 3, wrap=False, block='cmd')
        r.content('cp -R -n mongodb-{0}-enterprise-{1}-{2}/ mongodb'.format(builder, release, version), 3, wrap=False, block='cmd')

    r.newline(block='footer')

    return r

def generate_release_output(builder, platform, architecture, release):
    """ This is the contemporary version of the function used by the generate.py script"""

    r = RstCloth()

    r.directive('code-block', 'sh', block='header')
    r.newline(block='header')

    if architecture == 'core':
        r.content('curl -O http://downloads.mongodb.org/{0}/mongodb-{1}-{2}.tgz'.format(platform, builder, release), 3, wrap=False, block='cmd')
    else:
        r.content('curl -O http://downloads.10gen.com/linux/mongodb-{0}-enterprise-{1}-{2}.tgz'.format(builder, architecture, release), 3, wrap=False, block='cmd')
        r.content('tar -zxvf mongodb-{0}-enterprise-{1}-{2}.tgz'.format(builder, architecture, release), 3, wrap=False, block='cmd')
        r.content('cp -R -n mongodb-{0}-enterprise-{1}-{2}/ mongodb'.format(builder, architecture, release), 3, wrap=False, block='cmd')

    r.newline(block='footer')

    return r

def generate_release_untar(builder, release):
    r = RstCloth()

    r.directive('code-block', 'sh', block='header')
    r.newline(block='header')

    r.content('tar -zxvf mongodb-{0}-{1}.tgz'.format(builder, release), 3, wrap=False, block='cmd')

    return r

def generate_release_copy(builder, release):
    r = RstCloth()

    r.directive('code-block', 'sh', block='header')
    r.newline(block='header')

    r.content('mkdir -p mongodb', 3, wrap=False, block='cmd')
    r.content('cp -R -n mongodb-{0}-{1}/ mongodb'.format(builder, release), 3, wrap=False, block='cmd')

    return r

#################### Snippets for Inclusion in Installation Guides  ####################

# generate_release_output(builder, platform, version, release)

def _generate_release_ent(rel, target, release):
    r = generate_release_output( rel['type'], rel['type'].split('-')[0], rel['system'], release )
    r.write(target)
    logger.info('wrote release info file: ' + target)

def _generate_release_core(rel, target, release):
    r = generate_release_output( rel, rel.split('-')[0], 'core', release )
    r.write(target)
    logger.info('wrote release info file: ' + target)

def _generate_untar_core(rel, target, release):
    r = generate_release_untar(rel, release)
    r.write(target)
    logger.info('wrote release info file: ' + target)

def _generate_copy_core(rel, target, release):
    r = generate_release_copy(rel, release)
    r.write(target)
    logger.info('wrote release info file: ' + target)

def release_tasks(conf, app):
    if 'releases' not in conf.system.files.data:
        return

    if 'release' in conf.version:
        release_version = conf.version.release
    else:
        release_version = conf.version.published[0]

    rel_data = conf.system.files.data.releases

    deps = [ os.path.join(conf.paths.projectroot, conf.runstate.conf_path),
             os.path.abspath(__file__) ]

    for rel in rel_data['source-files']:
        target = os.path.join(conf.paths.projectroot,
                              conf.paths.includes,
                              'install-curl-release-{0}.rst'.format(rel))

        t = app.add('task')
        t.job = _generate_release_core
        t.args =  [ rel, target, release_version ]
        t.target = target
        t.dependency = deps
        t.description = 'generating release page {0}'.format(target)

        target = os.path.join(conf.paths.projectroot,
                              conf.paths.includes,
                              'install-untar-release-{0}.rst'.format(rel))

        t = app.add('task')
        t.job = _generate_untar_core
        t.args = [ rel, target, release_version ]
        t.target = target
        t.dependency = deps
        t.description = 'generating release page {0}'.format(target)

        target = os.path.join(conf.paths.projectroot,
                              conf.paths.includes,
                              'install-copy-release-{0}.rst'.format(rel))

        t = app.add('task')
        t.job = _generate_copy_core
        t.args = [ rel, target, release_version ]
        t.target = target
        t.dependency = deps
        t.description = 'generating release page {0}'.format(target)

    for rel in rel_data['subscription-build']:
        target = os.path.join(conf.paths.projectroot, conf.paths.includes,
                              'install-curl-release-ent-{0}.rst'.format(rel['system']))


        t = app.add('task')
        t.job = _generate_release_ent
        t.args = [ rel, target, release_version ]
        t.target = target
        t.dependency = deps
        t.description = 'generating release page {0}'.format(target)

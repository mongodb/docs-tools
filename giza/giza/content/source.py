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

import os.path
import logging
from shutil import rmtree

logger = logging.getLogger('giza.content.source')

from giza.content.dependencies import dump_file_hashes
from giza.tools.command import command
from giza.tools.files import InvalidFile

def transfer_source(conf, sconf):
    target = os.path.join(conf.paths.projectroot, conf.paths.branch_source)

    if not os.path.exists(target):
        os.makedirs(target)
        logger.debug('created directory for sphinx build: {0}'.format(target))
    elif not os.path.isdir(target):
        msg = '"{0}" exists and is not a directory'.format(target)
        logger.error(msg)
        raise InvalidFile(msg)

    source_dir = os.path.join(conf.paths.projectroot, conf.paths.source)

    # we don't want rsync to delete directories that hold generated content in
    # the target so we can have more incremental
    exclusions = "--exclude=" + ' --exclude='.join([ os.path.join('includes', 'steps'),
                                                     os.path.join('includes', 'toc') ])

    command('rsync --times --checksum --recursive {2} --delete {0}/ {1}'.format(source_dir, target, exclusions))

    source_exclusion(conf, sconf)
    dump_file_hashes(conf)

    logger.info('prepared source for sphinx build in {0}'.format(target))

def source_tasks(conf, sconf, app):
    t = app.add('task')
    t.job = transfer_source
    t.args = [conf, sconf]
    t.description = 'transferring source to {0}'.format(conf.paths.branch_source)
    logger.info('adding task to migrate source to {0}'.format(conf.paths.branch_source))

def source_exclusion(conf, sconf):
    for fn in sconf.excluded:
        fqfn = os.path.join(conf.paths.projectroot, conf.paths.branch_source, fn[1:])
        if os.path.exists(fqfn):
            if os.path.isdir(fqfn):
                rmtree(fqfn)
            else:
                os.remove(fqfn)
                logger.debug('redacted {0}'.format(fqfn))

    logger.info('redacted {0} files'.format(len(sconf.excluded)))

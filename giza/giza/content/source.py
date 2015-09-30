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

"""
Responsible for migrating content from the ``source`` repository to a directory
in ``build/<branch>/source`` (per-edition). These "proxy-source" directories
make it possible to:

- build while editing the source and changing sources,

- limit content generation in the source tree itself,

- avoid changing the ``mtime`` of files during branch changes to facilitate
  more incremental builds,

- have different versions of the source tree for different editions of the
  content (i.e. by redacting files or modifying the source,)

At the center of this operation is an ``rsync`` operation that uses check-summing
rather than timestampping to compare source and destination files.
"""

import os.path
import logging
import shutil
import shlex
import subprocess

import libgiza.task

from giza.tools.files import InvalidFile, safe_create_directory

logger = logging.getLogger('giza.content.source')

# Transfer Source Files


def transfer_source(conf, sconf):
    target = os.path.join(conf.paths.projectroot, conf.paths.branch_source)

    dir_exists = safe_create_directory(target)

    # this operation is just for messaging the above operation, and error'ing
    # appropriately.
    if dir_exists is True:
        logger.info('created directory for sphinx build: {0}'.format(target))
    elif not os.path.isdir(target):
        msg = '"{0}" exists and is not a directory'.format(target)
        logger.error(msg)
        raise InvalidFile(msg)

    source_dir = os.path.join(conf.paths.projectroot, conf.paths.source)
    image_dir = os.path.join(conf.paths.images[len(conf.paths.source) + 1:])

    exclusions = [os.path.join('includes', 'table'),
                  os.path.join('includes', 'generated'),
                  image_dir + os.path.sep + "*.png",
                  image_dir + os.path.sep + "*.rst",
                  image_dir + os.path.sep + "*.eps"]

    prefix_len = len(os.path.join(conf.paths.projectroot, conf.paths.branch_source)) + 1

    exclusions.extend([o for o in conf.system.content.output_directories(prefix_len) if o != "includes/changelogs"])

    # we don't want rsync to delete directories that hold generated content in
    # the target so we can have more incremental builds.
    exclusions = "--exclude=" + ' --exclude='.join(exclusions)

    cmd = 'rsync --links --checksum --recursive {2} --delete {0}/ {1}'
    cmd = cmd.format(source_dir, target, exclusions)

    try:
        subprocess.check_call(shlex.split(cmd))
    except subprocess.CalledProcessError as e:
        logger.error('source transfer rsync had error: ' + str(e.returncode))
        logger.info(cmd)

    # remove files from the source tree specified in the sphinx config for this
    # build.
    source_exclusion(conf, sconf)
    os.utime(target, None)

    logger.info('prepared and migrated source for sphinx build in {0}'.format(target))


def source_exclusion(conf, sconf):
    ct = 0
    if len(sconf.excluded) == 0:
        return

    for fn in sconf.excluded:
        fqfn = os.path.join(conf.paths.projectroot, conf.paths.branch_source, fn[1:])
        if os.path.isdir(fqfn):
            shutil.rmtree(fqfn)
            ct += 1
        elif os.path.isfile(fqfn):
            os.remove(fqfn)
            ct += 1
            logger.debug('redacted {0}'.format(fqfn))
        else:
            logger.warning('cannot redact non-existing file: ' + fqfn)

    logger.info('redacted {0} files'.format(ct))

# Transfer Images

# transfer all ``.eps`` images to the latex build directory because to generate
# "offset" resources, we declare the image in raw latex and Sphinx cannot migrate these images.


def transfer_images(conf, sconf):
    image_dir = os.path.join(conf.paths.projectroot, conf.paths.branch_images)
    if not os.path.isdir(image_dir):
        return False
    elif sconf.builder == 'latex':

        if 'edition' in sconf and sconf.edition is not None:
            builder_dir = '-'.join((sconf.builder, sconf.edition))
        else:
            builder_dir = sconf.builder

        builder_dir = os.path.join(conf.paths.projectroot, conf.paths.branch_output, builder_dir)
        safe_create_directory(builder_dir)

        cmd = ('rsync -am '
               '--include="*.png" --include="*.jpg" --include="*.eps" '
               '--exclude="*" {0}/ {1}')
        cmd = cmd.format(image_dir, builder_dir)

        with open(os.devnull, 'w') as null:
            for img_cmd in (shlex.split(cmd.replace('images', 'figures')),
                            shlex.split(cmd)):

                subprocess.call(img_cmd, stdout=null, stderr=null)

        logger.info('migrated images for latex build')

# Task Creators


def latex_image_transfer_tasks(conf, sconf):
    description = 'transferring images to build directory to {0}'.format(conf.paths.branch_source)

    return [libgiza.task.Task(job=transfer_images,
                              args=(conf, sconf),
                              target=True,
                              description=description)]


def source_tasks(conf, sconf):
    description = 'migrating source to {0}'.format(conf.paths.branch_source)

    return [libgiza.task.Task(job=transfer_source,
                              args=(conf, sconf),
                              target=os.path.join(conf.paths.branch_source),
                              description=description)]

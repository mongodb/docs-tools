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
Create and manipulate "packages" of build artifacts that can be used to quickly
share and deploy artifacts and build environment data.
"""

import logging
import datetime
import os
import tarfile
import contextlib
import urllib2

import argh
import libgiza.app

from giza.config.helper import fetch_config
from giza.tools.files import safe_create_directory, FileNotFoundError
from giza.operations.deploy import deploy_tasks

logger = logging.getLogger('giza.operations.packaging')

# Helper


def package_filename(target, conf):
    archive_path = os.path.join(conf.paths.projectroot, conf.paths.buildarchive)

    fn = [conf.project.name]

    if target is not None:
        tag = ''.join([i if i not in ['push', 'stage'] else '' for i in target.split('-')])
        if tag != '':
            fn.append(tag)

    fn.extend([conf.git.branches.current,
               datetime.datetime.utcnow().strftime('%s'),
               conf.git.commit[:8]])

    fn = os.path.join(archive_path, '-'.join(fn) + '.tar.gz')

    return fn


def create_archive(files_to_archive, tarball_name):
    # ready to write the tarball

    safe_create_directory(os.path.dirname(tarball_name))

    with tarfile.open(tarball_name, 'w:gz') as t:
        for fn, arc_fn in files_to_archive:
            t.add(name=fn, arcname=arc_fn)

# Worker Functions


def create_package(target, conf):
    logger.info('creating package for target "{0}"'.format(target))

    if target is None:
        pconf = conf.system.files.data.push[0]
        target = pconf['target']
    else:
        pconf = dict((item['target'], item) for item in conf.system.files.data.push)[target]

    files_to_archive = []

    if conf.project.branched is True:
        artifacts = (os.path.join(conf.paths.output,
                                  conf.git.branches.current),
                     conf.git.branches.current)
    else:
        artifacts = (os.path.join(conf.paths.projectroot,
                                  conf.paths.output,
                                  pconf['paths']['local']),
                     os.path.split(pconf['paths']['local'])[-1])

    files_to_archive.append(artifacts)

    if 'static' in pconf['paths']:
        files_to_archive.extend([
            (os.path.join(conf.paths.projectroot, conf.paths.public, path), path)
            for path in pconf['paths']['static']
            if os.path.exists(os.path.join(conf.paths.projectroot, conf.paths.public, path))
        ])

    archive_fn = package_filename(target, conf)

    create_archive(files_to_archive, archive_fn)

    logger.info('wrote build package to: {0}'.format(archive_fn))


def extract_package(conf):
    path = conf.runstate.package_path

    if conf.runstate.package_path.startswith('http'):
        path = fetch_package(path, conf)
    elif os.path.isfile(conf.runstate.package_path):
        path = conf.runstate.package_path
    else:
        m = "package {0} does not exist".format(conf.runstate.package_path)
        logger.critical(m)
        raise FileNotFoundError(m)

    with tarfile.open(path, "r:gz") as t:
        t.extractall(os.path.join(conf.paths.projectroot, conf.paths.public))


def fetch_package(path, conf):
    if path.startswith('http'):

        local_path = path.split('/')[-1]

        tar_path = os.path.join(conf.paths.projectroot,
                                conf.paths.buildarchive,
                                local_path)

        if not os.path.exists(tar_path):
            with contextlib.closing(urllib2.urlopen(path)) as u:
                with open(tar_path, 'w') as f:
                    f.write(u.read())
            logger.info('downloaded {0}'.format(local_path))
        else:
            logger.info('{0} exists locally, not downloading.'.format(local_path))

        return tar_path
    elif os.path.isfile(path):
        return path
    else:
        msg = 'no archive named "{0}" exists'.format(path)
        logger.error(msg)
        raise FileNotFoundError(msg)

# Command Entry Points


@argh.arg('--target', '-t', nargs="*", dest='push_targets')
@argh.expects_obj
def create(args):
    conf = fetch_config(args)

    for target in conf.runstate.push_targets:
        create_package(target, conf)


@argh.arg('--path', dest='package_path')
@argh.expects_obj
def unwind(args):
    conf = fetch_config(args)

    conf.runstate.package_path = fetch_package(conf.runstate.package_path, conf)
    logger.info('extracting package: ' + conf.runstate.package_path)
    extract_package(conf)
    logger.info('extracted package')


@argh.arg('--path', dest='package_path')
@argh.arg('--target', '-t', nargs=1, dest='push_targets')
@argh.arg('--dry-run', '-d', action='store_true', dest='dry_run')
@argh.expects_obj
def deploy(args):
    conf = fetch_config(args)

    conf.runstate.package_path = fetch_package(conf.runstate.package_path, conf)

    logger.info('extracting package: ' + conf.runstate.package_path)
    extract_package(conf)
    logger.info('extracted package')

    app = libgiza.app.BuildApp.new(pool_type=conf.runstate.runner,
                                   pool_size=conf.runstate.pool_size,
                                   force=conf.runstate.force)

    logger.info('beginning deploy now.')
    deploy_tasks(conf, app)

    if conf.runstate.dry_run is False:
        app.run()


@argh.arg('--path', dest='package_path')
@argh.expects_obj
def fetch(args):
    conf = fetch_config(args)

    if conf.runstate.package_path.startswith('http'):
        fetch_package(conf.runstate.pacage_path, conf)
    else:
        logger.error('{0} is not a url'.format(conf.runstate.package_path))
        raise SystemExit

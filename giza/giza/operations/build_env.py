# Copyright 2015 MongoDB, Inc.
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

import datetime
import logging
import os
import tarfile
import tempfile
import contextlib

import argh
import libgiza.task

from libgiza.app import BuildApp
from sphinx.application import Sphinx, ENV_PICKLE_FILENAME
from sphinx.builders.html import get_stable_hash

from giza.config.helper import fetch_config, get_builder_jobs
from giza.config.sphinx_config import avalible_sphinx_builders
from giza.operations.packaging import fetch_package
from giza.tools.files import safe_create_directory, FileNotFoundError

logger = logging.getLogger('giza.operations.build_env')

# Helpers


@contextlib.contextmanager
def cd(path):
    cur_dir = os.getcwd()

    os.chdir(path)

    yield

    os.chdir(cur_dir)


def is_git_dir(path):
    git_dir = ''.join([os.path.sep, '.git', os.path.sep])
    if git_dir in path:
        return True
    else:
        return False


def extract_package_at_root(path, conf):
    with cd(conf.paths.projectroot):
        with tarfile.open(path, "r:gz") as t:
            t.extractall()


def get_existing_builders(conf):
    return [b
            for b in avalible_sphinx_builders()
            if os.path.isdir(os.path.join(conf.paths.projectroot, conf.paths.branch_output, b))]


def env_package_worker(args, conf):
    # used by the make interface
    package_build_env(args.builder, args.editions_to_build, args.languages_to_build, conf)

# Core Workers


def package_build_env(builders, editions, languages, conf):
    arc_fn = '-'.join(['cache',
                       conf.project.name,
                       conf.git.branches.current,
                       datetime.datetime.utcnow().strftime('%s'),
                       conf.git.commit[:8]]) + ".tar.gz"
    archive_path = os.path.join(conf.paths.buildarchive, arc_fn)
    safe_create_directory(conf.paths.buildarchive)

    existing_archives = os.listdir(conf.paths.buildarchive)

    for arc in existing_archives:
        if conf.git.commit[:8] in arc:
            m = 'archive "{0}" exists for current git hash, not recreating'
            logger.warning(m.format(archive_path))
            return

    logger.debug("no archive for commit '{0}' continuing".format(conf.git.commit))

    with cd(conf.paths.projectroot):
        files_to_archive = set()

        for ((edition, language, builder), (rconf, sconf)) in get_builder_jobs(conf):
            files_to_archive.add(rconf.paths.branch_source)
            files_to_archive.add(os.path.join(rconf.paths.branch_output,
                                              sconf.build_output))
            files_to_archive.add(os.path.join(rconf.paths.branch_output,
                                              '-'.join(('doctrees', sconf.build_output))))
            files_to_archive.add(rconf.system.dependency_cache_fn)

        files_to_archive = list(files_to_archive)
        logger.info('prepped build cache archive. writing file now.')

        for fn in files_to_archive:
            if not os.path.exists(fn):
                raise FileNotFoundError(fn)

        try:
            with tarfile.open(archive_path, 'w:gz') as t:
                for fn in files_to_archive:
                    t.add(fn, exclude=is_git_dir)
            logger.info("created build-cache archive: " + archive_path)
        except Exception as e:
            os.remove(archive_path)
            logger.critical("failed to create archive: " + archive_path)
            logger.error(e)


def fix_build_env(builder, conf):
    """
    Given a builder name and the conf object, this function fixes the build
    artifacts for the current build to prevent a full rebuild. Currently
    re-pickles the environment and dumps the ``.buildinfo`` file in the build
    directory with the correct hashes.
    """

    fn = os.path.join(conf.paths.projectroot, conf.paths.branch_output, builder, '.buildinfo')
    logger.info('updating cache for: ' + builder)

    if not os.path.isfile(fn):
        return

    doctree_dir = os.path.join(conf.paths.projectroot,
                               conf.paths.branch_output,
                               "doctrees-" + builder)

    sphinx_app = Sphinx(srcdir=os.path.join(conf.paths.projectroot,
                                            conf.paths.branch_output, "source"),
                        confdir=conf.paths.projectroot,
                        outdir=os.path.join(conf.paths.projectroot,
                                            conf.paths.branch_output, builder),
                        doctreedir=doctree_dir,
                        buildername=builder,
                        status=tempfile.NamedTemporaryFile(),
                        warning=tempfile.NamedTemporaryFile())

    sphinx_app.env.topickle(os.path.join(doctree_dir, ENV_PICKLE_FILENAME))

    with open(fn, 'r') as f:
        lns = f.readlines()
        tags_hash_ln = None
        for ln in lns:
            if ln.startswith('tags'):
                tags_hash_ln = ln
                break

        if tags_hash_ln is None:
            tags_hash_ln = 'tags: ' + get_stable_hash(sorted(sphinx_app.tags))

    with open(fn, 'w') as f:
        config_dict = dict((name, sphinx_app.config[name])
                           for (name, desc) in sphinx_app.config.values.items()
                           if desc[1] == 'html')

        f.write('# Sphinx build info version 1')
        f.write('\n\n')  # current format requires an extra line here.
        f.write('config: ' + get_stable_hash(config_dict))
        f.write('\n')
        f.write(tags_hash_ln)
        f.write('\n')

# Task Creators


def fix_build_env_tasks(builders, conf):
    tasks = []

    message = "fix up sphinx environment for builder '{0}'"
    for builder in builders:
        t = libgiza.task.Task(job=fix_build_env,
                              args=(builder, conf),
                              target=True,
                              dependency=None,
                              description=message.format(builder))
        tasks.append(t)

    return tasks

# Entry Points


@argh.arg('--edition', '-e', nargs='*', dest='editions_to_build')
@argh.arg('--language', '-l', nargs='*', dest='languages_to_build')
@argh.arg('--builder', '-b', nargs='*', default='html')
@argh.expects_obj
def package(args):
    conf = fetch_config(args)

    package_build_env(builders=conf.runstate.builder,
                      editions=conf.runstate.editions_to_build,
                      languages=conf.runstate.languages_to_build,
                      conf=conf)


@argh.arg('--path', '-p', default=None, dest='_path')
@argh.expects_obj
def extract(args):
    conf = fetch_config(args)

    with BuildApp.new(pool_type=conf.runstate.runner,
                      pool_size=conf.runstate.pool_size,
                      force=conf.runstate.force).context() as app:
        path = fetch_package(conf.runstate._path, conf)
        extract_package_at_root(path, conf)

        builders = get_existing_builders(conf)
        app.extend_queue(fix_build_env_tasks(builders, conf))

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
Entry points that run the content generation tasks. Typically use these entry
points for testing and for prepopulating build directories. These functions do
not run in common practice.
"""

import logging

import argh

from giza.libgiza.app import BuildApp

from giza.config.helper import fetch_config, get_restricted_builder_jobs

from giza.content.assets import assets_tasks, assets_clean
from giza.content.images.tasks import image_tasks, image_clean
from giza.content.intersphinx import intersphinx_tasks, intersphinx_clean
from giza.content.table import table_tasks, table_clean
from giza.content.robots import robots_txt_tasks
from giza.content.redirects import make_redirect, redirect_tasks
from giza.content.migrations import migration_tasks, migration_clean

from giza.content.tocs.tasks import toc_tasks
from giza.content.apiargs.tasks import apiarg_tasks
from giza.content.examples.tasks import example_tasks
from giza.content.steps.tasks import step_tasks, step_clean
from giza.content.options.tasks import option_tasks, option_clean
from giza.content.release.tasks import release_tasks, release_clean
from giza.content.glossary.tasks import glossary_tasks, glossary_clean
from giza.content.changelog.tasks import changelog_tasks

from giza.operations.sphinx_cmds import sphinx_content_preperation, sphinx_builder_tasks

logger = logging.getLogger('giza.operations.generate')


@argh.arg('--edition', '-e')
@argh.expects_obj
def toc(args):
    c = fetch_config(args)

    with BuildApp.new(pool_type=c.runstate.runner,
                      pool_size=c.runstate.pool_size,
                      force=c.runstate.force).context() as app:
        app.extend_queue(toc_tasks(c))


@argh.arg('--edition', '-e')
@argh.arg('--clean', '-c', default=False, action="store_true", dest="clean_generated")
@argh.expects_obj
def steps(args):
    c = fetch_config(args)

    with BuildApp.new(pool_type=c.runstate.runner,
                      pool_size=c.runstate.pool_size,
                      force=c.runstate.force).context() as app:
        if c.runstate.clean_generated is True:
            app.extend_queue(step_clean(c))
        else:
            app.extend_queue(step_tasks(c))


@argh.arg('--clean', '-c', default=False, action="store_true", dest="clean_generated")
@argh.expects_obj
def options(args):
    c = fetch_config(args)

    with BuildApp.new(pool_type=c.runstate.runner,
                      pool_size=c.runstate.pool_size,
                      force=c.runstate.force).context() as app:

        if c.runstate.clean_generated is True:
            app.extend_queue(option_clean(c))
        else:
            app.extend_queue(option_tasks(c))


@argh.expects_obj
def api(args):
    c = fetch_config(args)

    with BuildApp.new(pool_type=c.runstate.runner,
                      pool_size=c.runstate.pool_size,
                      force=c.runstate.force).context() as app:
        app.extend_queue(apiarg_tasks(c))


@argh.arg('--clean', '-c', default=False, action="store_true", dest="clean_generated")
@argh.expects_obj
def assets(args):
    c = fetch_config(args)

    with BuildApp.new(pool_type=c.runstate.runner,
                      pool_size=c.runstate.pool_size,
                      force=c.runstate.force).context() as app:
        if c.runstate.clean_generated is True:
            app.extend_queue(assets_clean(c))
        else:
            app.extend_queue(assets_tasks(c))


@argh.arg('--edition', '-e', nargs='*', dest='editions_to_build')
@argh.arg('--language', '-l', nargs='*', dest='languages_to_build')
@argh.arg('--builder', '-b', nargs='*', default='html')
@argh.arg('--clean', '-c', default=False, action="store_true", dest="clean_generated")
@argh.expects_obj
def images(args):
    c = fetch_config(args)

    with BuildApp.new(pool_type=c.runstate.runner,
                      pool_size=c.runstate.pool_size,
                      force=c.runstate.force).context() as app:

        if c.runstate.clean_generated is True:
            app.extend_queue(image_clean(c))
        else:
            for (_, (bconf, sconf)) in get_restricted_builder_jobs(c):
                app.extend_queue(image_tasks(bconf, sconf))


@argh.arg('--clean', '-c', default=False, action="store_true", dest="clean_generated")
@argh.expects_obj
def intersphinx(args):
    c = fetch_config(args)

    with BuildApp.new(pool_type=c.runstate.runner,
                      pool_size=c.runstate.pool_size,
                      force=c.runstate.force).context() as app:
        if c.runstate.clean_generated is True:
            app.extend_queue(intersphinx_clean(c))
        else:
            app.extend_queue(intersphinx_tasks(c))


@argh.arg('--clean', '-c', default=False, action="store_true", dest="clean_generated")
@argh.aliases('primer', 'migrations')
@argh.expects_obj
def migration(args):
    c = fetch_config(args)

    with BuildApp.new(pool_type=c.runstate.runner,
                      pool_size=c.runstate.pool_size,
                      force=c.runstate.force).context() as app:
        if c.runstate.clean_generated is True:
            app.extend_queue(migration_clean(c))
        else:
            app.extend_queue(migration_tasks(c))


@argh.arg('--clean', '-c', default=False, action="store_true", dest="clean_generated")
@argh.expects_obj
def release(args):
    c = fetch_config(args)

    with BuildApp.new(pool_type=c.runstate.runner,
                      pool_size=c.runstate.pool_size,
                      force=c.runstate.force).context() as app:
        if c.runstate.clean_generated is True:
            app.extend_queue(release_clean(c))
        else:
            app.extend_queue(release_tasks(c))


@argh.arg('--clean', '-c', default=False, action="store_true", dest="clean_generated")
@argh.expects_obj
def tables(args):
    c = fetch_config(args)

    with BuildApp.new(pool_type=c.runstate.runner,
                      pool_size=c.runstate.pool_size,
                      force=c.runstate.force).context() as app:
        if c.runstate.clean_generated is True:
            app.extend_queue(table_clean(c))
        else:
            app.extend_queue(table_tasks(c))


@argh.expects_obj
def examples(args):
    c = fetch_config(args)

    with BuildApp.new(pool_type=c.runstate.runner,
                      pool_size=c.runstate.pool_size,
                      force=c.runstate.force).context() as app:
        app.extend_queue(example_tasks(c))


@argh.expects_obj
def changelogs(args):
    c = fetch_config(args)

    with BuildApp.new(pool_type=c.runstate.runner,
                      pool_size=c.runstate.pool_size,
                      force=c.runstate.force).context() as app:
        app.extend_queue(changelog_tasks(c))


@argh.arg('--clean', '-c', default=False, action="store_true", dest="clean_generated")
@argh.expects_obj
def glossary(args):
    c = fetch_config(args)

    with BuildApp.new(pool_type=c.runstate.runner,
                      pool_size=c.runstate.pool_size,
                      force=c.runstate.force).context() as app:
        if c.runstate.clean_generated is True:
            app.extend_queue(glossary_clean(c))
        else:
            app.extend_queue(glossary_tasks(c))


@argh.arg('--edition', '-e')
@argh.expects_obj
def robots(args):
    c = fetch_config(args)

    with BuildApp.new(pool_type=c.runstate.runner,
                      pool_size=c.runstate.pool_size,
                      force=c.runstate.force).context() as app:
        app.pool = 'serial'
        app.extend_queue(robots_txt_tasks(c))


@argh.arg('--edition', '-e')
@argh.arg('--print', '-p', default=False, action='store_true', dest='dry_run')
@argh.expects_obj
def redirects(args):
    c = fetch_config(args)

    if args.dry_run is True:
        print(''.join(make_redirect(c)))
    else:
        with BuildApp.new(pool_type=c.runstate.runner,
                          pool_size=c.runstate.pool_size,
                          force=c.runstate.force).context() as app:
            app.extend_queue(redirect_tasks(c))


@argh.arg('--edition', '-e', nargs='*', dest='editions_to_build')
@argh.arg('--language', '-l', nargs='*', dest='languages_to_build')
@argh.expects_obj
def source(args):
    args.builder = 'html'
    conf = fetch_config(args)

    with BuildApp.new(pool_type=conf.runstate.runner,
                      pool_size=conf.runstate.pool_size,
                      force=conf.runstate.force).context() as app:
        sphinx_content_preperation(app, conf)


@argh.arg('--edition', '-e', nargs='*', dest='editions_to_build')
@argh.arg('--language', '-l', nargs='*', dest='languages_to_build')
@argh.arg('--builder', '-b', nargs='*', default='html')
@argh.expects_obj
def sphinx(args):
    if args.runner == 'serial':
        args.serial_sphinx = True

    conf = fetch_config(args)
    logger.warning('not for production use: this expects that content generation is complete.')

    app = BuildApp.new(pool_type=conf.runstate.runner,
                       pool_size=conf.runstate.pool_size,
                       force=conf.runstate.force)

    r = sphinx_builder_tasks(app, conf)

    raise SystemExit(r)

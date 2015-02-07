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

from libgiza.app import BuildApp
from libgiza.task import Task
from giza.config.helper import fetch_config

from giza.content.assets import assets_tasks, assets_clean
from giza.content.images import image_tasks, image_clean
from giza.content.intersphinx import intersphinx_tasks, intersphinx_clean
from giza.content.table import table_tasks, table_clean
from giza.content.robots import robots_txt_tasks
from giza.content.redirects import make_redirect, redirect_tasks
from giza.content.tocs.tasks import toc_tasks
from giza.content.apiargs.tasks import apiarg_tasks
from giza.content.examples.tasks import example_tasks
from giza.content.steps.tasks import step_tasks, step_clean
from giza.content.options.tasks import option_tasks, option_clean
from giza.content.release.tasks import release_tasks, release_clean

from giza.content.primer import primer_migration_tasks
from giza.content.primer import clean as primer_clean

from giza.content.source import source_tasks
from giza.config.sphinx_config import render_sconf
from giza.content.dependencies import refresh_dependency_tasks

logger = logging.getLogger('giza.operations.generate')


@argh.arg('--edition', '-e')
@argh.expects_obj
def toc(args):
    c = fetch_config(args)

    with BuildApp.new(pool_type=c.runstate.runner,
                      pool_size=c.runstate.pool_size,
                      force=c.runstate.force).context() as app:
        for task in toc_tasks(c):
            app.add(task)


@argh.arg('--edition', '-e')
@argh.arg('--clean', '-c', default=False, action="store_true", dest="clean_generated")
@argh.expects_obj
def steps(args):
    c = fetch_config(args)

    with BuildApp.new(pool_type=c.runstate.runner,
                      pool_size=c.runstate.pool_size,
                      force=c.runstate.force).context() as app:
        if c.runstate.clean_generated is True:
            step_clean(c, app)
        else:
            app.extend_queue(step_tasks(c))


@argh.arg('--clean', '-c', default=False, action="store_true", dest="clean_generated")
@argh.expects_obj
def options(args):
    c = fetch_config(args)

    if c.runstate.clean_generated is True:
        option_clean(c)
    else:
        with BuildApp.new(pool_type=c.runstate.runner,
                          pool_size=c.runstate.pool_size,
                          force=c.runstate.force).context() as app:
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
            assets_clean(c, app)
        else:
            assets_tasks(c, app)


@argh.arg('--clean', '-c', default=False, action="store_true", dest="clean_generated")
@argh.expects_obj
def images(args):
    c = fetch_config(args)

    with BuildApp.new(pool_type=c.runstate.runner,
                      pool_size=c.runstate.pool_size,
                      force=c.runstate.force).context() as app:
        if c.runstate.clean_generated is True:
            image_clean(c, app)
        else:
            image_tasks(c, app)


@argh.arg('--clean', '-c', default=False, action="store_true", dest="clean_generated")
@argh.expects_obj
def intersphinx(args):
    c = fetch_config(args)

    with BuildApp.new(pool_type=c.runstate.runner,
                      pool_size=c.runstate.pool_size,
                      force=c.runstate.force).context() as app:
        if c.runstate.clean_generated is True:
            intersphinx_clean(c, app)
        else:
            intersphinx_tasks(c, app)


@argh.arg('--clean', '-c', default=False, action="store_true", dest="clean_generated")
@argh.expects_obj
def primer(args):
    c = fetch_config(args)

    with BuildApp.new(pool_type=c.runstate.runner,
                      pool_size=c.runstate.pool_size,
                      force=c.runstate.force).context() as app:
        if c.runstate.clean_generated is True:
            primer_clean(c, app)
        else:
            primer_migration_tasks(c, app)


@argh.arg('--clean', '-c', default=False, action="store_true", dest="clean_generated")
@argh.expects_obj
def release(args):
    c = fetch_config(args)

    with BuildApp.new(pool_type=c.runstate.runner,
                      pool_size=c.runstate.pool_size,
                      force=c.runstate.force).context() as app:
        if c.runstate.clean_generated is True:
            release_clean(c, app)
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
            table_clean(c, app)
        else:
            table_tasks(c, app)


@argh.expects_obj
def examples(args):
    c = fetch_config(args)

    with BuildApp.new(pool_type=c.runstate.runner,
                      pool_size=c.runstate.pool_size,
                      force=c.runstate.force).context() as app:
        app.extend_queue(example_tasks(c))


@argh.arg('--edition', '-e')
@argh.expects_obj
def robots(args):
    c = fetch_config(args)

    with BuildApp.new(pool_type=c.runstate.runner,
                      pool_size=c.runstate.pool_size,
                      force=c.runstate.force).context() as app:
        app.pool = 'serial'
        robots_txt_tasks(c, app)


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
            redirect_tasks(c, app)


@argh.arg('--edition', '-e')
@argh.arg('--language', '-l')
@argh.expects_obj
def source(args):
    conf = fetch_config(args)

    sconf = render_sconf(args.edition, 'html', args.language, conf)
    with BuildApp.new(pool_type=conf.runstate.runner,
                      pool_size=conf.runstate.pool_size,
                      force=conf.runstate.force).context() as app:

        with app.context() as pre_app:
            assets_tasks(conf, pre_app.add('app'))
            primer_migration_tasks(conf, pre_app)

        with app.context() as source_app:
            source_tasks(conf, sconf, source_app)

        for content, func in conf.system.content.task_generators:
            app.add(Task(job=func,
                         args=[conf],
                         target=True))

        content_generator_tasks = app.run()
        app.reset()

        for group in content_generator_tasks:
            if group is None:
                continue

            app.extend_queue(group)

        build_content_generation_tasks(conf, app.add('app'))
        refresh_dependency_tasks(conf, app.add('app'))

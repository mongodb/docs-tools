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

from giza.config.helper import fetch_config, get_builder_jobs, get_sphinx_build_configuration

from giza.content.assets import assets_tasks, assets_clean
from giza.content.images import image_tasks, image_clean
from giza.content.intersphinx import intersphinx_tasks, intersphinx_clean
from giza.content.table import table_tasks, table_clean
from giza.content.robots import robots_txt_tasks
from giza.content.redirects import make_redirect, redirect_tasks
from giza.content.primer import primer_migration_tasks
from giza.content.primer import clean as primer_clean

from giza.content.tocs.tasks import toc_tasks
from giza.content.apiargs.tasks import apiarg_tasks
from giza.content.examples.tasks import example_tasks
from giza.content.steps.tasks import step_tasks, step_clean
from giza.content.options.tasks import option_tasks, option_clean
from giza.content.release.tasks import release_tasks, release_clean

from giza.operations.sphinx_cmds import sphinx_content_preperation

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


@argh.arg('--clean', '-c', default=False, action="store_true", dest="clean_generated")
@argh.arg('--edition', '-e')
@argh.expects_obj
def images(args):
    c = fetch_config(args)

    with BuildApp.new(pool_type=c.runstate.runner,
                      pool_size=c.runstate.pool_size,
                      force=c.runstate.force).context() as app:
        if c.runstate.clean_generated is True:
            app.extend_queue(image_clean(c))
        else:
            app.extend_queue(image_tasks(c))


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
@argh.expects_obj
def primer(args):
    c = fetch_config(args)

    with BuildApp.new(pool_type=c.runstate.runner,
                      pool_size=c.runstate.pool_size,
                      force=c.runstate.force).context() as app:
        if c.runstate.clean_generated is True:
            app.extend_queue(primer_clean(c))
        else:
            app.extend_queue(primer_migration_tasks(c))


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


@argh.arg('--edition', '-e')
@argh.arg('--language', '-l')
@argh.expects_obj
def source(args):
    conf = fetch_config(args)
    args.builder = 'html'
    args.editions_to_build = conf.project.edition_list
    args.languages_to_build = ['en']

    builder_jobs = [((edition, language, builder),
                    get_sphinx_build_configuration(edition, language, builder, args))
                    for edition, language, builder in get_builder_jobs(conf)]

    with BuildApp.new(pool_type=conf.runstate.runner,
                      pool_size=conf.runstate.pool_size,
                      force=conf.runstate.force).context() as app:

        sphinx_content_preperation(builder_jobs, app, conf)

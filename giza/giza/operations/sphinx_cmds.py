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
Main controlling operations for running Sphinx builds.
"""

import logging
import argh

from giza.config.helper import fetch_config, get_builder_jobs, get_sphinx_build_configuration
from libgiza.app import BuildApp
from libgiza.task import Task

from giza.content.robots import robots_txt_tasks
from giza.content.includes import includes_tasks
from giza.content.images import image_tasks
from giza.content.intersphinx import intersphinx_tasks
from giza.content.table import table_tasks
from giza.content.hash import hash_tasks
from giza.content.source import source_tasks, latex_image_transfer_tasks
from giza.content.dependencies import refresh_dependency_tasks, dump_file_hash_tasks
from giza.content.sphinx import sphinx_tasks, output_sphinx_stream, finalize_sphinx_build
from giza.content.redirects import redirect_tasks
from giza.content.primer import primer_migration_tasks
from giza.content.assets import assets_tasks

from giza.tools.timing import Timer

logger = logging.getLogger('giza.operations.sphinx')


@argh.arg('--edition', '-e', nargs='*', dest='editions_to_build')
@argh.arg('--language', '-l', nargs='*', dest='languages_to_build')
@argh.arg('--builder', '-b', nargs='*', default='html')
@argh.arg('--serial_sphinx', action='store_true')
@argh.named('sphinx')
@argh.expects_obj
def main(args):
    """
    Use Sphinx to generate build artifacts. Can generate artifacts for multiple
    output types, content editions and translations.
    """
    conf = fetch_config(args)

    app = BuildApp.new(pool_type=conf.runstate.runner,
                       pool_size=conf.runstate.pool_size,
                       force=conf.runstate.force)

    with Timer("full sphinx build process"):
        # In general we try to avoid passing the "app" object between functions
        # and mutating it at too many places in the stack (although in earlier
        # versions this was the primary idiom). This call is a noted exception,
        # and makes it possible to run portions of this process in separate
        # targets.

        sphinx_publication(conf, app)

# sphinx_publication is its own function because it's called as part of some
# giza.operations.deploy tasks (i.e. ``push``).
def sphinx_publication(conf, app):
    """
    :arg Configuration c: A :class:`giza.config.main.Configuration()` object.

    :arg BuildApp app: A :class:`libgiza.app.BuildApp()` object.

    Adds all required tasks to build a Sphinx site. Specifically:

    1. Iterates through the (language * builder * edition) combination and adds
       tasks to generate the content in the
       <build>/<branch>/source<-edition<-language>> directory. There is one
       version of the <build>/<branch>/source directory for every
       language/edition combination, but multiple builders can use the same
       diretory as needed.

    2. Add a task to run the ``sphinx-build`` task.

    3. Run all tasks in proper order.

    4. Process and print the output of ``sphinx-build``.

    :return: The sum of all return codes from all ``sphinx-build`` tasks. All
             non-zero statuses represent errors.

    :rtype: int
    """

    # assemble a list to generate tasks in the form of:
    # ((edition, language, builder), (conf, sconf))
    builder_jobs = [((edition, language, builder),
                    get_sphinx_build_configuration(edition, language, builder, conf.runstate))
                    for edition, language, builder in get_builder_jobs(conf)]

    # call function to prepare the source/content. Seperate so that we can also
    # call this from/as the giza.operations.generate.source() entry point.
    sphinx_content_preperation(builder_jobs, app, conf)

    # sphinx-build tasks are separated into their own app.
    sphinx_app = app.sub_app()
    for ((edition, language, builder), (build_config, sconf)) in builder_jobs:
        sphinx_job = sphinx_tasks(sconf, build_config)

        sphinx_job.finalizers = finalize_sphinx_build(sconf, build_config)
        sphinx_app.extend_queue(sphinx_job)

        logger.info("adding builder job for {0} ({1}, {2})".format(builder, language, edition))

    # Connect the special sphinx app to the main app.
    app.add(sphinx_app)

    logger.info("sphinx build configured, running the build now.")
    app.run()
    logger.info("sphinx build complete.")

    logger.info('builds finalized. sphinx output and errors to follow')

    # process the sphinx build. These oeprations allow us to de-duplicate
    # messages between builds.
    sphinx_results = [o for o in sphinx_app.results
                      if not isinstance(o, (list, bool, type(None)))]
    sphinx_output = '\n'.join([o[1] for o in sphinx_results])
    output_sphinx_stream(sphinx_output, conf)

    # if entry points return this value, giza will inherit the sum of the Sphinx
    # build return codes.
    ret_code = sum([o[0] for o in sphinx_results])
    return ret_code


def sphinx_content_preperation(builder_jobs, app, conf):
    # Download embedded git repositories and then run migrations before doing
    # anything else.
    with app.context() as prep_app:
        assets = assets_tasks(conf)
        prep_app.extend_queue(assets)

        migrations = primer_migration_tasks(conf)
        prep_app.extend_queue(migrations)

    # Copy all source to the ``build/<branch>/source`` directory.
    with Timer('migrating source to build'):
        with app.context(randomize=True) as source_app:
            source_app.randomize

            build_source_copies = set()
            for (_, (build_config, sconf)) in builder_jobs:
                if build_config.paths.branch_source not in build_source_copies:
                    build_source_copies.add(build_config.paths.branch_source)

                    source_app.extend_queue(source_tasks(build_config, sconf))

    # load all generated content and create tasks.
    with Timer('loading generated content'):
        build_source_copies = set()
        for (_, (build_config, sconf)) in builder_jobs:
            if build_config.paths.branch_source not in build_source_copies:
                build_source_copies.add(build_config.paths.branch_source)

                for content, func in build_config.system.content.task_generators:
                    app.add(Task(job=func,
                                 args=[build_config],
                                 target=True))

        app.randomize = True
        results = app.run()
        app.reset()

        for task_group in results:
            app.extend_queue(task_group)

    build_source_copies = set()
    for ((edition, language, builder), (build_config, sconf)) in builder_jobs:
        if build_config.paths.branch_source not in build_source_copies:
            # only do these tasks once per-language+edition combination
            build_source_copies.add(build_config.paths.branch_source)

            for content_generator in (robots_txt_tasks, intersphinx_tasks, includes_tasks,
                                      table_tasks, hash_tasks, redirect_tasks, image_tasks):
                app.extend_queue(content_generator(build_config))

            dependency_refresh_app = app.add('app')
            dependency_refresh_app.extend_queue(refresh_dependency_tasks(build_config))

            # once the source is prepared, we dump a dict with md5 hashes of all
            # files, so we can do better dependency resolution the next time.
            app.extend_queue(dump_file_hash_tasks(build_config))

            # we transfer images to the latex directory directly because offset
            # images are included using raw latex, and Sphinx doesn't know how
            # to copy images in this case.
            app.extend_queue(latex_image_transfer_tasks(build_config, sconf))

            msg = 'added source tasks for ({0}, {1}, {2}) in {3}'
            logger.info(msg.format(builder, language, edition, build_config.paths.branch_source))

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
import os.path
import argh

from giza.config.helper import fetch_config, get_builder_jobs, register_content_generators
from giza.core.app import BuildApp

logger = logging.getLogger('giza.operations.sphinx')

from giza.content.robots import robots_txt_tasks
from giza.content.includes import includes_tasks
from giza.content.images import image_tasks
from giza.content.intersphinx import intersphinx_tasks
from giza.content.param import api_tasks
from giza.content.table import table_tasks
from giza.content.hash import hash_tasks
from giza.content.source import source_tasks, latex_image_transfer_tasks
from giza.content.toc import toc_tasks
from giza.content.dependencies import refresh_dependency_tasks, dump_file_hash_tasks
from giza.content.sphinx import sphinx_tasks, output_sphinx_stream, finalize_sphinx_build
from giza.content.redirects import redirect_tasks

from giza.config.sphinx_config import render_sconf
from giza.tools.timing import Timer

@argh.arg('--edition', '-e', nargs='*', dest='editions_to_build')
@argh.arg('--language', '-l', nargs='*',dest='languages_to_build')
@argh.arg('--builder', '-b', nargs='*', default='html')
@argh.arg('--serial_sphinx', action='store_true')
@argh.named('sphinx')
@argh.expects_obj
def main(args):
    """
    Use Sphinx to generate build artifacts. Can generate artifacts for multiple
    output types, content editions and translations.
    """
    c = fetch_config(args)
    app = BuildApp(c)

    with Timer("full sphinx build process"):
        return sphinx_publication(c, args, app)

## sphinx_publication is its own function because it's called as part of some
## giza.operations.deploy tasks (i.e. ``push``).

def sphinx_publication(c, args, app):
    """
    :arg Configuration c: A :class:`giza.config.main.Configuration()` object.

    :arg RuntimeStateConfig args: A :class:`giza.config.runtime.RuntimeState()` object.

    :arg BuildApp app: A :class:`giza.core.app.BuildApp()` object.

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

    # sphinx-build tasks are separated into their own app.
    sphinx_app = BuildApp(c)
    sphinx_app.pool = app.pool

    # this loop will produce an app for each language/edition/builder combination
    build_source_copies = set()

    for edition, language, builder in get_builder_jobs(c):
        build_config, sconf = get_sphinx_build_configuration(edition, language, builder, args)

        # only do these tasks once per-language+edition combination
        if build_config.paths.branch_source not in build_source_copies:
            build_source_copies.add(build_config.paths.branch_source)

            prep_app = app.add('app')
            prep_app.conf = build_config

            # this is where we add tasks to transfer the source into the
            # ``build/<branch>/source`` directory.
            source_tasks(build_config, sconf, prep_app)
            # this function runs the entire prep_app compiled until now, so that
            # the content generation tasks are created properly

            # these operation groups each execute in isolation of each-other and should.
            build_content_generation_tasks(build_config, prep_app.add('app'))
            refresh_dependency_tasks(build_config, prep_app.add('app'))

            # once the source is prepared, we dump a dict with md5 hashes of all
            # files, so we can do better dependency resolution the next time.
            dump_file_hash_tasks(build_config, prep_app)

            # we transfer images to the latex directory directly because offset
            # images are included using raw latex, and Sphinx doesn't know how
            # to copy images in this case.
            latex_image_transfer_tasks(build_config, sconf, prep_app)

            msg = 'added source tasks for ({0}, {1}, {2}) in {3}'
            logger.info(msg.format(builder, language, edition, build_config.paths.branch_source))

        # Add sphinx tasks for this builder/language/edition combination
        sphinx_tasks(sconf, build_config, sphinx_app)
        logger.info("adding builder job for {0} ({1}, {2})".format(builder, language, edition))

    # Connect the special sphinx app to the main app.
    app.add(sphinx_app)

    logger.info("sphinx build configured, running the build now.")
    app.run()
    logger.info("sphinx build complete.")

    logger.info('builds finalized. sphinx output and errors to follow')

    # process the sphinx build. These oeprations allow us to de-duplicate
    # messages between builds.
    sphinx_output = '\n'.join([ o[1] for o in sphinx_app.results ])
    output_sphinx_stream(sphinx_output, c)

    # if entry points return this value, giza will inherit the sum of the Sphinx
    # build return codes.
    ret_code = sum([ o[0] for o in sphinx_app.results ])
    return ret_code

def get_sphinx_build_configuration(edition, language, builder, args):
    """
    Given an ``edition``, ``language`` and ``builder`` strings and the runtime
    arguments, return copies of the configuration (``conf``) and sphinx
    configuration (``sconf``) objects.
    """

    args.language = language
    args.edition = edition
    args.builder = builder

    conf = fetch_config(args)
    sconf = render_sconf(edition, builder, language, conf)

    return conf, sconf

def build_content_generation_tasks(conf, app):
    """
    :param Configuration conf: The current build configuration object.

    :param BuildApp app: A :class:`~giza.core.app.BuildApp()` object.

    Add tasks to the ``app`` for all tasks that modify the content in
    ``build/<branch>/source`` directory.
    """
    app.randomize = True

    with Timer("adding content tasks"):
        for content, func in conf.system.content.task_generators:
            t = app.add('task')
            t.job = func
            t.args = [conf]
            t.target = True

        results = app.run()

        for content_generator_tasks in results:
            app.extend_queue(content_generator_tasks)

    robots_txt_tasks(conf, app)
    intersphinx_tasks(conf, app)
    includes_tasks(conf, app)
    table_tasks(conf, app)
    hash_tasks(conf, app)
    api_tasks(conf, app)
    redirect_tasks(conf, app)
    image_tasks(conf, app)

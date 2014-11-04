import logging
import os.path
import argh
import itertools

from giza.config.helper import fetch_config
from giza.core.app import BuildApp

logger = logging.getLogger('giza.operations.sphinx')

from giza.content.robots import robots_txt_tasks
from giza.content.includes import includes_tasks
from giza.content.assets import assets_tasks
from giza.content.images import image_tasks
from giza.content.intersphinx import intersphinx_tasks
from giza.content.release import release_tasks
from giza.content.options import option_tasks
from giza.content.param import api_tasks
from giza.content.table import table_tasks
from giza.content.hash import hash_tasks
from giza.content.source import source_tasks
from giza.content.toc import toc_tasks
from giza.content.examples.tasks import example_tasks
from giza.content.steps.tasks import step_tasks
from giza.content.dependencies import refresh_dependency_tasks, dump_file_hash_tasks
from giza.content.sphinx import sphinx_tasks, output_sphinx_stream, finalize_sphinx_build
from giza.content.primer import primer_migration_tasks
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
    c = fetch_config(args)
    app = BuildApp(c)

    sphinx_publication(c, args, app)

## sphinx_publication is its own function because it's called as part of some
## giza.operations.deploy tasks (i.e. ``push``).

def sphinx_publication(c, args, app):
    """
    :arg Configuration c: A :class:`giza.config.main.Configuration()` object.

    :arg RuntimeStateConfig args: A :class:`giza.config.runtime.RuntimeState()` object.

    :arg BuildApp app: A :class:`giza.core.app.BuildApp()` object.

    Adds all required tasks to build a Sphinx site. Specifically:

    1. Adds a group of early-stage tasks to generate content (e.g. assets,
       intersphinx) that do not have dependencies.

    2. Iterates through the (language * builder * edition) combination and adds
       tasks to generate the content in the
       <build>/<branch>/source<-edition<-language>> directory. There is one
       version of the <build>/<branch>/source directory for every
       language/edition combination, but multiple builders can use the same
       diretory as needed.

    3. Add a task to run the ``sphinx-build`` task.

    4. Run all tasks in proper order.

    5. Process and print the output of ``sphinx-build``.

    :return: The sum of all return codes from all ``sphinx-build`` tasks. All
             non-zero statuses represent errors.

    :rtype: int
    """

    build_prep_tasks(c, app)

    # sphinx-build tasks are separated into their own app.
    sphinx_app = BuildApp(c)
    sphinx_app.pool = app.pool

    # this loop will produce an app for each language/edition/builder combination
    build_source_copies = set()

    jobs = [a for a in itertools.product(c.runstate.editions_to_build, c.runstate.languages_to_build, c.runstate.builder)]
    for edition, language, builder in jobs:
        build_config, sconf = get_sphinx_build_configuration(edition, language, builder, args)

        # only do these tasks once per-language+edition combination
        if build_config.paths.branch_source not in build_source_copies:
            build_source_copies.add(build_config.paths.branch_source)

            prep_app = app.add('app')
            prep_app.conf = build_config

            source_tasks(build_config, sconf, prep_app)
            build_content_generation_tasks(build_config, prep_app.add('app'))
            refresh_dependency_tasks(build_config, prep_app.add('app'))
            dump_file_hash_tasks(build_config, prep_app)

            msg = 'prepared source for ({0}, {1}, {2}) in {3}'
            logger.info(msg.format(builder, language, edition, build_config.paths.branch_source))

        sphinx_tasks(sconf, build_config, sphinx_app)
        logger.info("adding builder job for {0} ({1}, {2})".format(builder, language, edition))

    app.add(sphinx_app)

    logger.info("sphinx build configured, running the build now.")
    app.run()
    logger.info("sphinx build complete.")

    logger.info('builds finalized. sphinx output and errors to follow')

    sphinx_output = '\n'.join([ o[1] for o in sphinx_app.results ])
    ret_code = sum([ o[0] for o in sphinx_app.results ])
    output_sphinx_stream(sphinx_output, c)

    return ret_code

def get_sphinx_build_configuration(edition, language, builder, args):
    args.language = language
    args.edition = edition
    args.builder = builder

    conf = fetch_config(args)
    sconf = render_sconf(edition, builder, language, conf)

    return conf, sconf

def build_prep_tasks(conf, app):
    primer_migration_tasks(conf, app)
    robots_txt_tasks(conf, app)
    assets_tasks(conf, app)
    includes_tasks(conf, app)
    intersphinx_tasks(conf, app)
    release_tasks(conf, app)
    api_tasks(conf, app)
    table_tasks(conf, app)

def build_content_generation_tasks(conf, app):
    hash_tasks(conf, app)
    redirect_tasks(conf, app)
    image_tasks(conf, app)
    step_tasks(conf, app)
    toc_tasks(conf, app)
    option_tasks(conf, app)
    example_tasks(conf, app)

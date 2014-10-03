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
from giza.content.steps import steps_tasks
from giza.content.dependencies import refresh_dependency_tasks
from giza.content.sphinx import sphinx_tasks, output_sphinx_stream, finalize_sphinx_build
from giza.content.primer import primer_migration_tasks
from giza.content.redirects import redirect_tasks

from giza.config.sphinx_config import render_sconf

@argh.arg('--edition', '-e', nargs='*', dest='editions_to_build')
@argh.arg('--language', '-l', nargs='*',dest='languages_to_build')
@argh.arg('--builder', '-b', nargs='*', default='html')
@argh.arg('--serial_sphinx', action='store_true', default=False)
@argh.named('sphinx')
def main(args):
    c = fetch_config(args)
    app = BuildApp(c)

    sphinx_publication(c, args, app)

def sphinx_publication(c, args, app):
    build_prep_tasks(c, app)

    # this loop will produce an app for each language/edition/builder combination
    build_source_copies = set()
    sphinx_app = BuildApp(c)
    sphinx_app.pool = app.pool

    jobs = itertools.product(args.editions_to_build, args.languages_to_build, args.builder)
    for edition, language, builder in jobs:
        args.language = language
        args.edition = edition
        args.builder = builder
        build_config = fetch_config(args)

        prep_app = app.add('app')
        prep_app.conf = build_config

        primer_app = prep_app.add('app')
        primer_migration_tasks(build_config, primer_app)

        sconf = render_sconf(edition, builder, language, build_config)

        if build_config.paths.branch_source not in build_source_copies:
            build_source_copies.add(build_config.paths.branch_source)
            source_tasks(build_config, sconf, prep_app)

            source_app = prep_app.add('app')
            build_content_generation_tasks(build_config, source_app)
            refresh_dependency_tasks(build_config, prep_app)

        sphinx_tasks(sconf, build_config, sphinx_app)
        logger.info("adding builder job for {0} ({1}, {2})".format(builder, language, edition))

    app.add(sphinx_app)

    logger.info("sphinx build setup, running now.")
    app.run()
    logger.info("sphinx build complete.")

    logger.info('builds finalized. sphinx output and errors to follow')

    sphinx_output = '\n'.join([ o[1] for o in sphinx_app.results ])
    ret_code = sum([ o[0] for o in sphinx_app.results ])
    output_sphinx_stream(sphinx_output, c)

    ret_code = 0

    return ret_code

def build_prep_tasks(conf, app):
    image_tasks(conf, app)
    robots_txt_tasks(conf, app)
    assets_tasks(conf, app)
    includes_tasks(conf, app)
    intersphinx_tasks(conf, app)
    release_tasks(conf, app)
    option_tasks(conf, app)
    api_tasks(conf, app)
    table_tasks(conf, app)

def build_content_generation_tasks(conf, app):
    hash_tasks(conf, app)
    redirect_tasks(conf, app)
    steps_tasks(conf, app.add('app'))
    toc_tasks(conf, app)
    example_tasks(conf, app)

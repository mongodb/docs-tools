import logging
import os.path
import argh
import itertools

from giza.config.main import Configuration
from giza.app import BuildApp

logger = logging.getLogger(os.path.basename(__file__))

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
from giza.content.source import source_tasks, exclusion_tasks
from giza.content.toc import toc_tasks
from giza.content.steps import steps_tasks
from giza.content.dependencies import refresh_dependency_tasks
from giza.content.sphinx import run_sphinx

from giza.tools.config import render_sphinx_config
from giza.tools.serialization import ingest_yaml_doc

@argh.arg('--edition', '-e', nargs='*', dest='editions_to_build')
@argh.arg('--language', '-l', nargs='*',dest='languages_to_build')
@argh.arg('--builder', '-b', nargs='*', default='html', dest='sphinx_builders')
def sphinx(args):
    c = Configuration()
    c.ingest(args.conf_path)
    c.runstate = args

    app = BuildApp(c)

    # run this once per entire build
    build_setup = app.add('app')
    build_setup.pool = 'thread'

    robots_txt_tasks(c, build_setup)
    assets_tasks(c, build_setup)
    image_tasks(c, build_setup)
    includes_tasks(c, build_setup)

    # TODO: add primer migration here (build_setup)

    # content generation
    content_gen = app.add('app')
    content_gen.pool = 'process'
    intersphinx_tasks(c, content_gen)
    release_tasks(c, content_gen)
    option_tasks(c, content_gen)
    api_tasks(c, content_gen)
    table_tasks(c, content_gen)
    hash_tasks(c, content_gen)

    # this loop will produce an app for each language/edition/builder combination
    build_source_copies = []
    for lang, edition, builder in itertools.product(c.runstate.editions_to_build,
                                                    c.runstate.languages_to_build,
                                                    c.runstate.sphinx_builders):
        args.language = lang
        args.edition = edition
        args.sphinx_builder = builder

        build_config = Configuration()
        build_config.ingest(args.conf_path)
        build_config.runstate = args

        build_app = BuildApp(build_config)
        build_app.pool = 'thread'
        prep_app = build_app.add('app')
        prep_app.pool = 'process'

        sconf_base = render_sphinx_config(ingest_yaml_doc(os.path.join(c.paths.projectroot, c.paths.builddata, 'sphinx.yaml')))
        sconf = sconf_base[builder]
        sconf['edition'] = edition
        if lang is not None:
            sconf['language'] = lang

        if build_config.paths.branch_source not in build_source_copies:
            build_source_copies.append(build_config.paths.branch_source)
            source_tasks(build_config, prep_app)

            source_app = prep_app.add('app')
            toc_tasks(build_config, source_app)
            steps_tasks(build_config, source_app)
            exclusion_tasks(build_config, sconf, source_app)

            refresh_dependency_tasks(build_config, prep_app)

        sphinx_task = build_app.add('task')
        sphinx_task.job = run_sphinx
        sphinx_task.args = [builder, sconf, build_config]
        sphinx_task.description = 'building {0} with sphinx'.format(builder)

        # TODO: add sphinx finalize to a new app (finalize_app)

        logger.info("adding builder job for {0} ({1}, {2})".format(builder, lang, edition))
        app.add(build_app)

    logger.info("sphinx build setup, running now.")
    app.run()
    logger.info("sphinx build complete.")

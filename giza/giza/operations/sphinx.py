import logging
import os.path
import argh
import itertools

from giza.config.helper import fetch_config
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
    c = fetch_config(args)
    app = BuildApp(c)

    build_setup = app.add('app')
    build_setup.pool = 'thread'
    build_prep_tasks(c, build_setup)

    # content generation
    content_gen = app.add('app')
    content_gen.pool = 'process'
    source_content_generation_tasks(c, content_gen)

    # this loop will produce an app for each language/edition/builder combination
    build_source_copies = set()
    for lang, edition, builder in itertools.product(c.runstate.editions_to_build,
                                                    c.runstate.languages_to_build,
                                                    c.runstate.sphinx_builders):
        args.language = lang
        args.edition = edition
        args.sphinx_builder = builder
        build_config = fetch_config(args)

        build_app = BuildApp(build_config)
        build_app.pool = 'thread'
        # primer_migrate_tasks(build_config, build_app)
        prep_app = build_app.add('app')
        prep_app.pool = 'process'

        sconf = render_sconf(edition, builder, language, build_config)

        if build_config.paths.branch_source not in build_source_copies:
            build_source_copies.add(build_config.paths.branch_source)
            source_tasks(build_config, prep_app)

            source_app = prep_app.add('app')
            build_content_generation_tasks(sconf, build_config, source_app)

            refresh_dependency_tasks(build_config, prep_app)

        sphinx_tasks(sconf, build_config, build_app)
        # TODO: add sphinx finalize to a new app (finalize_app)

        logger.info("adding builder job for {0} ({1}, {2})".format(builder, lang, edition))
        app.add(build_app)

    logger.info("sphinx build setup, running now.")
    app.run()
    logger.info("sphinx build complete.")

def render_sconf(edition, builder, language, conf):
    sconf_path = os.path.join(conf.paths.projectroot, conf.paths.builddata, 'sphinx.yaml')

    sconf_base = render_sphinx_config(ingest_yaml_doc(sconf_path))
    sconf = sconf_base[builder]

    sconf['edition'] = edition
    sconf['builder'] = builder

    if lang is not None:
        sconf['language'] = language

    return sconf

def build_prep_tasks(conf, app):
    robots_txt_tasks(conf, app)
    assets_tasks(conf, app)
    image_tasks(conf, app)
    includes_tasks(conf, app)

def source_content_generation_tasks(conf, app):
    intersphinx_tasks(conf, app)
    release_tasks(conf, app)
    option_tasks(conf, app)
    api_tasks(conf, app)
    table_tasks(conf, app)
    hash_tasks(conf, app)

def build_content_generation_tasks(sconf, conf, app):
    toc_tasks(conf, app)
    steps_tasks(conf, app)
    exclusion_tasks(conf, sconf, app)

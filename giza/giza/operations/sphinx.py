import logging
import os.path
import argh
import itertools

from giza.config.helper import fetch_config
from giza.app import BuildApp

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
from giza.content.source import source_tasks, exclusion_tasks
from giza.content.toc import toc_tasks
from giza.content.steps import steps_tasks
from giza.content.dependencies import refresh_dependency_tasks
from giza.content.sphinx import sphinx_tasks, output_sphinx_stream
from giza.content.primer import primer_migration_tasks

from giza.config.sphinx import render_sphinx_config
from giza.serialization import ingest_yaml_doc

@argh.arg('--edition', '-e', nargs='*', dest='editions_to_build')
@argh.arg('--language', '-l', nargs='*',dest='languages_to_build')
@argh.arg('--builder', '-b', nargs='*', default='html', dest='sphinx_builders')
def sphinx(args):
    c = fetch_config(args)
    app = BuildApp(c)
    app.pool = 'thread'

    build_prep_tasks(c, app)

    # this loop will produce an app for each language/edition/builder combination
    build_source_copies = set()
    sphinx_app = BuildApp(c)
    sphinx_app.pool = app.pool
    jobs = itertools.product(args.editions_to_build, args.languages_to_build, args.sphinx_builders)
    for edition, language, builder in jobs:
        args.language = language
        args.edition = edition
        args.sphinx_builder = builder
        build_config = fetch_config(args)

        prep_app = app.add('app')
        prep_app.conf = build_config

        primer_app = prep_app.add('app')
        primer_migration_tasks(build_config, primer_app)

        sconf = render_sconf(edition, builder, language, build_config)

        if build_config.paths.branch_source not in build_source_copies:
            build_source_copies.add(build_config.paths.branch_source)
            source_tasks(build_config, prep_app)

            source_app = prep_app.add('app')
            build_content_generation_tasks(sconf, build_config, source_app)

            refresh_dependency_tasks(build_config, prep_app)

        sphinx_tasks(sconf, build_config, sphinx_app)
        logger.info("adding builder job for {0} ({1}, {2})".format(builder, language, edition))

    app.add(sphinx_app)

    logger.info("sphinx build setup, running now.")
    app.run()
    output_sphinx_stream(sphinx_app.results, c)
    logger.info("sphinx build complete.")

def render_sconf(edition, builder, language, conf):
    sconf_path = os.path.join(conf.paths.projectroot, conf.paths.builddata, 'sphinx.yaml')

    # this operation is really expensive relative to what we need and how often
    # we have to do it:
    sconf_base = render_sphinx_config(ingest_yaml_doc(sconf_path))

    if edition is not None:
        builder = '-'.join([builder, edition])

    sconf = sconf_base[builder]

    sconf['edition'] = edition
    if 'builder' not in sconf:
        sconf['builder'] = builder

    if language is not None:
        sconf['language'] = language

    return sconf

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
    hash_tasks(conf, app)

def build_content_generation_tasks(sconf, conf, app):
    steps_tasks(conf, app.add('app'))
    toc_tasks(conf, app)
    exclusion_tasks(conf, sconf, app)

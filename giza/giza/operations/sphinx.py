import logging
import os.path
import argh
import itertools

from giza.config.main import Configuration
from giza.app import BuildApp

logger = logging.getLogger(os.path.basename(__file__))

from giza.content.robots import robots_txt_builder
from giza.content.includes import write_include_index
from giza.content.assets import assets_setup
from giza.content.images import image_tasks
from giza.content.intersphinx import intersphinx_tasks
from giza.content.release import release_tasks
from giza.content.options import option_tasks
from giza.content.param import api_tasks
from giza.content.table import table_tasks
from giza.content.hash import hash_tasks
from giza.content.source import transfer_source

@argh.arg('--edition', '-e', nargs='*', dest='editions_to_build')
@argh.arg('--language', '-l', nargs='*',dest='languages_to_build')
@argh.arg('--builder', '-b', nargs='*', default='html', dest='sphinx_builders')
def sphinx(args):
    c = Configuration()
    c.ingest(args.conf_path)
    c.runstate = args

    # the larger overarching process
    app = BuildApp(c)

    # run this once per entire build
    build_setup = app.add('app')

    if os.path.exists(os.path.join(c.paths.projectroot, c.paths.builddata, 'robots.yaml')):
        t = build_setup.add('task')
        t.job = robots_txt_builder
        t.args = [ os.path.join(c.paths.projectroot,
                                c.paths.public,
                                'robots.txt'), c ]

    if c.assets is not None:
        for asset in c.assets:
            path = os.path.join(c.paths.projectroot, asset.path)
            logger.info('adding asset resolution job for {0}'.format(path))
            t = build_setup.add('task')
            t.job = assets_setup
            t.args = { 'path': path,
                       'branch': asset.branch,
                       'repo': asset.repository }

    image_tasks(c, build_setup)

    if (os.path.exists(os.path.join(c.paths.projectroot, c.paths.includes)) and
        os.path.exists(os.path.join(c.paths.projectroot, c.paths.source, 'meta'))):
        t = build_setup.add('task')
        t.job = write_include_index
        t.args = [ c ]

    content_gen = app.add('app')
    intersphinx_tasks(c, content_gen)
    release_tasks(c, content_gen)
    option_tasks(c, content_gen)
    api_tasks(c, content_gen)
    table_tasks(c, content_gen)
    hash_tasks(c, content_gen)

    # TODO: add primer migration here (build_setup)

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
        prep_app = build_app.add('app')

        # TODO: make the sphinx config (sconf) a thing here

        if build_config.paths.branch_source not in build_source_copies:
            t = prep_app.add('task')
            t.job = transfer_source
            t.args = [build_config]
            t.description = 'transferring source to {0}'.format(build_config.paths.branch_source)
            build_source_copies.append(build_config.paths.branch_source)
            logger.info('adding task to migrate source to {0}'.format(build_config.paths.branch_source))

            source_app = prep_app.add('app')
            # TODO: build TOCs (in source_prep)

            # TODO: build steps (in source_prep)

            # TODO: remove excluded files (in source_prep)

            # TODO: refresh_dependencies(build_conf) (task in prep_app)

        # TODO: port logic from utils.sphinx.workers.sphinx_build() adding
        # sphinx-build Task() to (build_app)

        # TODO: add sphinx finalize to a new app (finalize_app)

        logger.info("adding builder job for {0} ({1}, {2})".format(builder, lang, edition))
        app.add(build_app)

    logger.info("sphinx build setup, running now.")
    app.run()
    logger.info("sphinx build complete.")

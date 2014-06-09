import logging
import os.path
import argh
import itertools

from giza.config.main import Configuration
from giza.app import BuildApp

logger = logging.getLogger(os.path.basename(__file__))

from giza.content.robots import robots_txt_builder
from giza.content.includes import write_include_index

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

    # eventually this should be moved into the per-builder jobs.
    if (os.path.exists(os.path.join(c.paths.projectroot, c.paths.includes)) and
        os.path.exists(os.path.join(c.paths.projectroot, c.paths.source, 'meta'))):
        t = build_setup.add('task')
        t.job = write_include_index
        t.args = [ c ]

    ## TODO: add assets to build_setup here

    # this loop will produce an app for each language/edition/builder combination
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

        ## construct the builder with per-builder tasks

        logger.info("adding builder for {0} ({1}, {2})".format(builder, lang, edition))
        app.add(build_app)

    app.run()

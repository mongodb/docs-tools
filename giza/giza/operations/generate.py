import logging

logger = logging.getLogger('giza.operations.generate')

import argh

from giza.app import BuildApp
from giza.config.helper import fetch_config

from giza.content.assets import assets_tasks, assets_clean
from giza.content.images import image_tasks, image_clean
from giza.content.intersphinx import intersphinx_tasks, intersphinx_clean
from giza.content.options import option_tasks, option_clean
from giza.content.param import api_tasks, api_clean
from giza.content.steps import steps_tasks, steps_clean
from giza.content.table import table_tasks, table_clean
from giza.content.toc import toc_tasks, toc_clean

from giza.content.primer import primer_migration_tasks
from giza.content.primer import clean as primer_clean

@argh.arg('--edition', '-e')
@argh.arg('--clean', '-c', default=False, action="store_true", dest="clean_generated")
def toc(args):
    c = fetch_config(args)
    app = BuildApp(c)

    if c.runstate.clean_generated is True:
        toc_clean(c)
    else:
        toc_tasks(c, app)

    app.run()

@argh.arg('--edition', '-e')
@argh.arg('--clean', '-c', default=False, action="store_true", dest="clean_generated")
def steps(args):
    c = fetch_config(args)
    app = BuildApp(c)

    if c.runstate.clean_generated is True:
        steps_clean(conf, app)
    else:
        steps_tasks(c, app)

    app.run()

@argh.arg('--clean', '-c', default=False, action="store_true", dest="clean_generated")
def options(args):
    c = fetch_config(args)
    app = BuildApp(c)

    if c.runstate.clean_generated is True:
        option_clean(c)
    else:
        option_tasks(c, app)

    app.run()

@argh.arg('--clean', '-c', default=False, action="store_true", dest="clean_generated")
def api(args):
    c = fetch_config(args)
    app = BuildApp(c)

    if c.runstate.clean_generated is True:
        api_clean(c, app)
    else:
        api_tasks(c, app)

    app.run()

@argh.arg('--clean', '-c', default=False, action="store_true", dest="clean_generated")
def assets(args):
    c = fetch_config(args)
    app = BuildApp(c)

    if c.runstate.clean_generated is True:
        assets_clean(c, app)
    else:
        asset_tasks(c, app)

    app.run()

@argh.arg('--clean', '-c', default=False, action="store_true", dest="clean_generated")
def images(args):
    c = fetch_config(args)
    app = BuildApp(c)

    if c.runstate.clean_generated is True:
        image_clean(c, app)
    else:
        image_tasks(c, app)

    app.run()

@argh.arg('--clean', '-c', default=False, action="store_true", dest="clean_generated")
def intersphinx(args):
    c = fetch_config(args)
    app = BuildApp(c)

    if c.runstate.clean_generated is True:
        intersphinx_clean(c, app)
    else:
        intersphinx_tasks(c, app)

    app.run()

@argh.arg('--clean', '-c', default=False, action="store_true", dest="clean_generated")
def primer(args):
    c = fetch_config(args)

    if c.runstate.clean_generated is True:
        primer_clean(c)
    else:
        app = BuildApp(c)
        primer_migration_tasks(c, app)
        app.run()

@argh.arg('--clean', '-c', default=False, action="store_true", dest="clean_generated")
def tables(args):
    c = fetch_config(args)
    app = BuildApp(c)

    if c.runstate.clean_generated is True:
        table_clean(c, app)
    else:
        table_tasks(c, app)

    app.run()

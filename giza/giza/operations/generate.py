import logging
import os.path

logger = logging.getLogger(os.path.basename(__file__))

import argh

from giza.app import BuildApp
from giza.config.helper import fetch_config
from giza.content.toc import toc_tasks
from giza.content.steps import steps_tasks
from giza.content.options import option_tasks
from giza.content.param import api_tasks
from giza.content.assets import assets_tasks
from giza.content.images import image_tasks
from giza.content.table import table_tasks
from giza.content.intersphinx import intersphinx_tasks

from giza.content.primer import primer_migration_tasks
from giza.content.primer import clean as primer_clean

@argh.arg('--edition', '-e')
def toc(args):
    c = fetch_config(args)
    app = BuildApp(c)

    toc_tasks(c, app)

    app.run()

@argh.arg('--edition', '-e')
def steps(args):
    c = fetch_config(args)
    app = BuildApp(c)

    steps_tasks(c, app)

    app.run()

def options(args):
    c = fetch_config(args)
    app = BuildApp(c)

    option_tasks(c, app)

    app.run()

def api(args):
    c = fetch_config(args)
    app = BuildApp(c)

    api_tasks(c, app)

    app.run()

def assets(args):
    c = fetch_config(args)
    app = BuildApp(c)

    asset_tasks(c, app)

    app.run()

def images(args):
    c = fetch_config(args)
    app = BuildApp(c)

    image_tasks(c, app)

    app.run()

def intersphinx(args):
    c = fetch_config(args)
    app = BuildApp(c)

    intersphinx_tasks(c, app)

    app.run()

@argh.arg('--clean', '-c', default=False, dest="primer_clean")
def primer(args):
    c = fetch_config(args)

    if c.runstate.primer_clean is True:
        primer_clean(c)
    else:
        app = BuildApp(c)
        primer_migration_tasks(c, app)
        app.run()


def tables(args):
    c = fetch_config(args)
    app = BuildApp(c)

    table_tasks(c, app)

    app.run()

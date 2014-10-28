import logging

logger = logging.getLogger('giza.operations.generate')

import argh

from giza.core.app import BuildApp
from giza.config.helper import fetch_config
from giza.tools.files import rm_rf

from giza.content.assets import assets_tasks, assets_clean
from giza.content.images import image_tasks, image_clean
from giza.content.intersphinx import intersphinx_tasks, intersphinx_clean
from giza.content.options import option_tasks, option_clean
from giza.content.param import api_tasks, api_clean
from giza.content.table import table_tasks, table_clean
from giza.content.toc import toc_tasks, toc_clean
from giza.content.robots import robots_txt_tasks
from giza.content.redirects import make_redirect, redirect_tasks
from giza.content.examples.tasks import example_tasks
from giza.content.steps.tasks import step_tasks, step_clean

from giza.content.primer import primer_migration_tasks
from giza.content.primer import clean as primer_clean

@argh.arg('--edition', '-e')
@argh.arg('--clean', '-c', default=False, action="store_true", dest="clean_generated")
@argh.expects_obj
def toc(args):
    c = fetch_config(args)

    if c.runstate.clean_generated is True:
        toc_clean(c)
    else:
        app = BuildApp(c)
        toc_tasks(c, app)
        app.run()

@argh.arg('--edition', '-e')
@argh.arg('--clean', '-c', default=False, action="store_true", dest="clean_generated")
@argh.expects_obj
def steps(args):
    c = fetch_config(args)
    app = BuildApp(c)

    if c.runstate.clean_generated is True:
        step_clean(c, app)
    else:
        step_tasks(c, app)

    app.run()

@argh.arg('--clean', '-c', default=False, action="store_true", dest="clean_generated")
@argh.expects_obj
def options(args):
    c = fetch_config(args)

    if c.runstate.clean_generated is True:
        option_clean(c)
    else:
        app = BuildApp(c)
        option_tasks(c, app)
        app.run()

@argh.arg('--clean', '-c', default=False, action="store_true", dest="clean_generated")
@argh.expects_obj
def api(args):
    c = fetch_config(args)
    app = BuildApp(c)

    if c.runstate.clean_generated is True:
        api_clean(c, app)
    else:
        api_tasks(c, app)

    app.run()

@argh.arg('--clean', '-c', default=False, action="store_true", dest="clean_generated")
@argh.expects_obj
def assets(args):
    c = fetch_config(args)
    app = BuildApp(c)

    if c.runstate.clean_generated is True:
        assets_clean(c, app)
    else:
        assets_tasks(c, app)

    app.run()

@argh.arg('--clean', '-c', default=False, action="store_true", dest="clean_generated")
@argh.expects_obj
def images(args):
    c = fetch_config(args)
    app = BuildApp(c)

    if c.runstate.clean_generated is True:
        image_clean(c, app)
    else:
        image_tasks(c, app)

    app.run()

@argh.arg('--clean', '-c', default=False, action="store_true", dest="clean_generated")
@argh.expects_obj
def intersphinx(args):
    c = fetch_config(args)
    app = BuildApp(c)

    if c.runstate.clean_generated is True:
        intersphinx_clean(c, app)
    else:
        intersphinx_tasks(c, app)

    app.run()

@argh.arg('--clean', '-c', default=False, action="store_true", dest="clean_generated")
@argh.expects_obj
def primer(args):
    c = fetch_config(args)
    app = BuildApp(c)

    if c.runstate.clean_generated is True:
        primer_clean(c, app)
    else:
        primer_migration_tasks(c, app)

    app.run()

@argh.arg('--clean', '-c', default=False, action="store_true", dest="clean_generated")
@argh.expects_obj
def tables(args):
    c = fetch_config(args)
    app = BuildApp(c)

    if c.runstate.clean_generated is True:
        table_clean(c, app)
    else:
        table_tasks(c, app)

    app.run()

@argh.expects_obj
def examples(args):
    c = fetch_config(args)
    app = BuildApp(c)

    example_tasks(c, app)

    app.run()

@argh.arg('--edition', '-e')
@argh.expects_obj
def robots(args):
    c = fetch_config(args)
    app = BuildApp(c)
    app.pool = 'serial'

    robots_txt_tasks(c, app)

    app.run()

@argh.arg('--edition', '-e')
@argh.arg('--print', '-p', default=False, action='store_true', dest='dry_run')
@argh.expects_obj
def redirects(args):
    c = fetch_config(args)

    if args.dry_run is True:
        print(''.join(make_redirect(c)))
    else:
        app = BuildApp(c)

        redirect_tasks(c, app)
        app.run()

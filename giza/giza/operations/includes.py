import os
import logging
import json

import argh

logger = logging.getLogger('giza.operations.includes')

from giza.app import BuildApp
from giza.config.helper import fetch_config

from giza.includes import (included_once, included_recusively,
                           includes_masked, include_files,
                           include_files_unused, changed_includes)

## Helper

def render_for_console(data):
    print(json.dumps(data, indent=3))

## Entry Points

def recursive(args):
    c = fetch_config(args)

    render_for_console(included_recusively(conf=c))

def changed(args):
    c = fetch_config(args)

    render_for_console(changed_includes(conf=c))

def once(args):
    c = fetch_config(args)

    render_for_console(included_once(conf=c))

def unused(args):
    c = fetch_config(args)

    render_for_console(included_files_unused(conf=c))

def list(args):
    c = fetch_config(args)

    render_for_console(include_files(conf=conf).keys())

@argh.arg('--filter', '-f', default=None, dest="include_mask")
def graph(args):
    c = fetch_config(args)

    if c.runstate.include_mask is None:
        render_for_console(include_files(conf=c))
    else:
        if c.runstate.include_mask.startswith(c.paths.source):
            mask = mask[6:]
        elif c.runstate.include_mask.startswith('/' + c.paths.source):
            mask = mask[7:]
        else:
            mask = c.runstate.include_mask

        render_for_console(includes_masked(mask=mask, conf=conf))

def clean(args):
    c = fetch_config(args)

    for fn in include_files_unused(conf=c):
        fn = os.path.join(conf.paths.source, fn[1:])
        if os.path.exists(fn):
            os.remove(fn)
            logger.info("removed {0}, which was an unused include file.".format(fn))
        else:
            logger.error('{0} does not exist'.format(fn))

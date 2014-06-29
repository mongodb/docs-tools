import logging
import os

logger = logging.getLogger(os.path.basename(__file__))

import json

from fabric.api import task

from fabfile.utils.config import lazy_conf
from fabfile.utils.includes import (included_once, included_recusively,
                            includes_masked, include_files,
                            include_files_unused, changed_includes)

@task
def names():
    "Returns the names of all included files as a list."
    conf = lazy_conf()

    render_for_console(include_files(conf=conf).keys())

@task
def graph():
    "Returns the full directed dependency graph for a all included files."

    conf = lazy_conf()

    render_for_console(include_files(conf=conf))

@task
def recursive():
    "Returns a list of included files that include other files."
    conf = lazy_conf()

    render_for_console(included_recusively(conf=conf))

@task
def single():
    "Returns a list of included files that are only used once."
    conf = lazy_conf()

    render_for_console(included_once(conf=conf))

@task
def unused():
    "Returns a list of included files that are never used."
    conf = lazy_conf()

    render_for_console(include_files_unused(conf=conf))

@task
def filter(mask):
    "Returns a subset of the dependency graph based on a required 'mask' argument."
    conf = lazy_conf()

    mask = resolve_mask(mask)

    render_for_console(includes_masked(mask=mask, conf=conf))

@task
def changed():
    "Returns a list of all files that include a file that has changed since the last commit."
    conf = lazy_conf()
    render_for_console(changed_includes(conf))

@task
def cleanup():
    conf = lazy_conf()

    for fn in include_files_unused(conf=conf):
        fn = os.path.join(conf.paths.source, fn[1:])
        if os.path.exists(fn):
            os.remove(fn)
            logger.info("removed {0}, which was an unused include file.".format(fn))
        else:
            logger.error('{0} does not exist'.format(fn))

########## Helper Functions ##########

def resolve_mask(mask):
    if mask.startswith('source'):
        mask = mask[6:]
    if mask.startswith('/source'):
        mask = mask[7:]

    return mask

def render_for_console(data):
    print(json.dumps(data, indent=3))

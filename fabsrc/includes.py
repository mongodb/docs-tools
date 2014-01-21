import json

from fabric.api import task

from utils.includes import (included_once, included_recusively,
                            includes_masked, include_files,
                            include_files_unused, changed_includes)

@task
def names():
    "Returns the names of all included files as a list."

    render_for_console(include_files().keys())

@task
def graph():
    "Returns the full directed dependency graph for a all included files."

    render_for_console(include_files())

@task
def recursive():
    "Returns a list of included files that include other files."

    render_for_console(included_recusively())

@task
def single():
    "Returns a list of included files that are only used once."

    render_for_console(included_once())

@task
def unused():
    "Returns a list of included files that are never used."

    render_for_console(include_files_unused())

@task
def filter(mask):
    "Returns a subset of the dependency graph based on a required 'mask' argument."

    mask = resolve_mask(mask)

    render_for_console(includes_masked(mask))

@task
def changed():
    "Returns a list of all files that include a file that has changed since the last commit."
    render_for_console(changed_includes())

########## Helper Functions ##########

def resolve_mask(mask):
    if mask.startswith('source'):
        mask = mask[6:]
    if mask.startswith('/source'):
        mask = mask[7:]

    return mask

def render_for_console(data):
    if not isinstance(data, list):
        data = list(data)

    print(json.dumps(data, indent=3))

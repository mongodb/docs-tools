# Copyright 2014 MongoDB, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Diagnostic operation that displays the majority of the current configuration
object.
"""

import json
import logging
import sys

import giza
import argh
import giza.libgiza

from giza.config.helper import fetch_config

logger = logging.getLogger('giza.operations.configuration')


@argh.named('version')
@argh.expects_obj
def report_version(args):
    "Returns current version of giza"

    print("giza: " + giza.__version__)
    print("giza.libgiza: " + giza.libgiza.__version__)


@argh.arg('config_target', nargs='*')
@argh.arg('--simple', action='store_true')
@argh.arg('--conf_path', '-c')
@argh.arg('--edition', '-e')
@argh.arg('--language', '-l')
@argh.named('config')
@argh.expects_obj
def render_config(args):
    """Returns configuration object for diagnostic purposes."""

    c = fetch_config(args)

    # the following values are rendered lazily. we list them here so that the
    # final object will be useful to inspect.
    [c.git.commit, c.paths.public, c.git.branches.current,
     c.git.branches.manual, c.git.branches.published,
     c.paths.branch_output, c.paths.buildarchive,
     c.paths.branch_source, c.paths.branch_staging,
     c.paths.branch_images, c.paths.branch_includes,
     c.version.published, c.version.stable, c.version.upcoming,
     c.project.edition, c.deploy, c.paths.global_config,
     c.project.branched, c.system.dependency_cache,
     c.system.dependency_cache_fn, c.paths.public_site_output,
     c.system.content, c.runstate.runner, c.runstate.force,
     c.system.files, c.system.files.paths, c.system.files.data,
     c.system.files.data.integration, c.paths.htaccess]

    # Print out everything
    if not args.config_target:
        print(json.dumps(c.dict(), indent=2))
        return

    query = args.config_target[0]
    cursor = c

    for segment in query.split('.'):
        try:
            if hasattr(cursor, segment):
                cursor = getattr(cursor, segment)
            else:
                cursor = cursor[segment]
        except (KeyError, TypeError):
            logger.fatal('No key "%s" in configuration', query)
            sys.exit(1)

    # Convert a giza.config.system.SystemConfigData object into a dict
    if hasattr(cursor, 'dict'):
        cursor = cursor.dict()

    if args.simple:
        try:
            result = ' '.join(cursor)
        except TypeError:
            logger.fatal('Cannot represent %s with --simple', query)
            sys.exit(1)
    else:
        result = json.dumps(cursor, indent=2)

    print(result)

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
import argh

import giza
import libgiza

from giza.config.helper import fetch_config


@argh.named('version')
@argh.expects_obj
def report_version(args):
    "Returns current version of giza"

    print("giza: " + giza.__version__)
    print("libgiza: " + libgiza.__version__)


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
     c.paths.htaccess]

    print('--- ' + "str of config object >>>")
    print(json.dumps(c.dict(), indent=3))
    print('---  <<<')

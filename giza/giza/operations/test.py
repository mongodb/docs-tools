# Copyright 2015 MongoDB, Inc.
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

import argh
import os
import logging
import libgiza.git

import giza.content.assets
import giza.config.helper
import giza.config.main
import giza.tools.files

logger = logging.getLogger('giza.operations.test')

def pprint(doc):
    import json

    print(json.dumps(doc, indent=3, sort_keys=True))

@argh.expects_obj
@argh.named('test')
def integration_main(args):
    try:
        conf = giza.config.helper.fetch_config(args)
    except RuntimeError:
        path = os.path.join('data', 'build_config.yaml')
        if not os.path.isfile(path):
            logger.warning('must run test from the docs-tools repo, or a giza project directory.')
            raise SystemExit(-1)
        else:
            args.conf_path = os.path.join('data', 'build_config.yaml')

            conf = giza.config.main.Configuration()
            conf.ingest(args.conf_path)
            conf.runstate = args
            conf.paths.projectroot = os.getcwd()

    build_path = os.path.join(conf.paths.projectroot, conf.paths.output)
    giza.tools.files.safe_create_directory(build_path)

    for project in conf.test.projects:
        path = os.path.join(build_path, project.project)

        print("# testing " + project.project)
        if os.path.isdir(path):
            g = libgiza.git.GitRepo(path)
            # g.pull()
        else:
            g = libgiza.git.GitRepo()
            # g.clone(remote=project.uri, repo_path=path)
            g.path = path


        for branch in project.branches:
            print(branch)

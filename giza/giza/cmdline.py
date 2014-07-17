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

import json
import logging

logger = logging.getLogger('giza.main')

import argh

from giza.config.runtime import RuntimeStateConfig

import giza.operations.generate
import giza.operations.includes
from giza.operations.configuration import render_config
from giza.operations.clean import clean
from giza.operations.git import apply_patch, pull_rebase, cherry_pick
from giza.operations.sphinx import sphinx
from giza.operations.deploy import deploy, push

def get_base_parser():
    parser = argh.ArghParser()
    parser.add_argument('--level', '-l',
                        choices=['debug', 'warning', 'info', 'critical', 'error'],
                        default='info')
    parser.add_argument('--serial', '-s', default=None, dest='runner', const='serial', action='store_const')
    parser.add_argument('--force', '-f', default=False, action='store_true')

    return parser

def main():
    parser = get_base_parser()

    commands = [
        render_config,
        clean,
        sphinx,
        deploy, push
    ]

    argh.add_commands(parser, commands)
    argh.add_commands(parser, [apply_patch, pull_rebase, cherry_pick], namespace='git')

    generate_commands = [
        giza.operations.generate.api,
        giza.operations.generate.assets,
        giza.operations.generate.images,
        giza.operations.generate.intersphinx,
        giza.operations.generate.options,
        giza.operations.generate.primer,
        giza.operations.generate.steps,
        giza.operations.generate.tables,
        giza.operations.generate.toc,
    ]

    argh.add_commands(parser, generate_commands, namespace='generate')

    include_commands = [
        giza.operations.includes.recursive,
        giza.operations.includes.changed,
        giza.operations.includes.once,
        giza.operations.includes.unused,
        giza.operations.includes.list,
        giza.operations.includes.graph,
        giza.operations.includes.clean,
    ]

    argh.add_commands(parser, include_commands, namespace='includes')

    args = RuntimeStateConfig()
    argh.dispatch(parser, namespace=args)

if __name__ == '__main__':
    main()

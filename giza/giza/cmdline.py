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
import giza.operations.packaging
import giza.operations.git
import giza.operations.tx
import giza.operations.translate
import giza.operations.make

from giza.operations.configuration import render_config
from giza.operations.clean import clean
from giza.operations.sphinx import sphinx
from giza.operations.deploy import deploy, push
from giza.operations.quickstart import make_project

def get_base_parser():
    parser = argh.ArghParser()
    parser.add_argument('--level', '-l',
                        choices=['debug', 'warning', 'info', 'critical', 'error'],
                        default='info')
    parser.add_argument('--serial', '-s', default=None, dest='runner', const='serial', action='store_const')
    parser.add_argument('--thread', default=None, dest='runner', const='thread', action='store_const')
    parser.add_argument('--event', default=None, dest='runner', const='event', action='store_const')
    parser.add_argument('--force', '-f', default=False, action='store_true')

    return parser

def main():
    parser = get_base_parser()

    commands = [
        make_project,
        render_config,
        clean,
        sphinx,
        deploy, push,
        giza.operations.make.main
    ]
    argh.add_commands(parser, commands)

    git_commands = [
        giza.operations.git.apply_patch,
        giza.operations.git.pull_rebase,
        giza.operations.git.cherry_pick,
        giza.operations.git.merge,
    ]
    argh.add_commands(parser, git_commands, namespace='git')

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
        giza.operations.generate.examples,
        giza.operations.generate.redirects
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

    packaging_commands = [
        giza.operations.packaging.fetch,
        giza.operations.packaging.unwind,
        giza.operations.packaging.create,
        giza.operations.packaging.deploy,
    ]
    argh.add_commands(parser, packaging_commands, namespace='package')

    translate_commands = [
            giza.operations.translate.create_corpora,
            giza.operations.translate.build_translation_model,
            giza.operations.translate.model_results,
            giza.operations.translate.merge_translations,
            giza.operations.translate.po_to_corpus,
            giza.operations.translate.dict_to_corpus,
            giza.operations.translate.translate_po,
            giza.operations.translate.translate_text_doc,
            giza.operations.translate.flip_text,
            giza.operations.translate.auto_approve_obvious_po,
    ]
    argh.add_commands(parser, translate_commands, namespace='translate')

    translation_commands = [
        giza.operations.tx.check_orphaned,
        giza.operations.tx.update_translations,
        giza.operations.tx.pull_translations,
        giza.operations.tx.push_translations,
    ]
    argh.add_commands(parser, translation_commands, namespace='tx')

    args = RuntimeStateConfig()
    argh.dispatch(parser, namespace=args)

if __name__ == '__main__':
    main()

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
Entry points for managing Moses-based machine translation processes.
"""

import os
import sys
import logging
import smtplib
from email.mime.text import MIMEText

import argh
import yaml
import itertools

from giza.translate.corpora import create_hybrid_corpora, create_corpus_from_po, create_corpus_from_dictionary
from giza.translate.model import build_model, setup_train, setup_tune, setup_test
from giza.translate.model_results import aggregate_model_data
from giza.translate.utils import merge_files, flip_text_direction
from giza.translate.translation import translate_po_files, translate_file, auto_approve_po_entries
from giza.config.corpora import CorporaConfig
from giza.config.helper import fetch_config
from giza.config.translate import TranslateConfig
from giza.core.app import BuildApp

logger = logging.getLogger('giza.operations.translate')

@argh.arg('--config', '-c', default=None, dest="t_corpora_config")
@argh.named('create-corpora')
@argh.expects_obj
def create_corpora(args):
    conf = fetch_config(args)

    if args.t_corpora_config is None:
        cconf = conf.system.files.data.corpora
    elif os.path.isfile(args.t_corpora_config):
        cconf = CorporaConfig(args.t_corpora_config)
    else:
        logger.error(args.t_corpora_config + " doesn't exist")
        return

    if os.path.exists(cconf.container_path):
        logger.error(cconf.container_path + " already exists. Please delete it or change the container and try again")
        return

    create_hybrid_corpora(cconf)


@argh.arg('--config', '-c', default=None, dest="t_translate_config")
@argh.named('model-results')
@argh.expects_obj
def model_results(args):
    conf = fetch_config(args)

    if args.t_translate_config is None:
        tconf = conf.system.files.data.translate
    elif os.path.isfile(args.t_translate_config):
        tconf = TranslateConfig(args.t_translate_config, conf)
    else:
        logger.error(args.t_translate_config + " doesn't exist")
        return

    aggregate_model_data(tconf.paths.project)


@argh.arg('--output', '-o', default=None, dest='t_output_file')
@argh.arg('--input', '-i', required=True, default=None, nargs='*', dest='t_input_files')
@argh.named('merge')
@argh.expects_obj
def merge_translations(args):
    annotation_list = ['- ', '+ ', '~ ', '> ', '= ', '* ', '# ', '$ ', '^ ', '% ', '& ', '@ ']
    merge_files(args.t_output_file, args.t_input_files, annotation_list)


@argh.arg('--po', default=None, required=True, dest='t_input_file')
@argh.arg('--source', '-s', default="source_corpus.txt", dest='t_source')
@argh.arg('--target', '-t', default="target_corpus.txt", dest='t_target')
@argh.named('po-to-corpus')
@argh.expects_obj
def po_to_corpus(args):
    create_corpus_from_po(args.t_input_file, args.t_source, args.t_target)


@argh.arg('--dict', required=True, default=None, dest='t_input_file')
@argh.arg('--source', '-s', default="source_corpus.txt", dest='t_source')
@argh.arg('--target', '-t', default="target_corpus.txt", dest='t_target')
@argh.named('dict-to-corpus')
@argh.expects_obj
def dict_to_corpus(args):
    create_corpus_from_dictionary(args.t_input_file, args.t_source, args.t_target)


@argh.arg('--config', '-c', default=None, dest="t_translate_config")
@argh.arg('--po', required=True, default=None, dest='t_input_file')
@argh.arg('--protected', '-p', default=None, dest='t_protected_regex')
@argh.named('translate-po')
@argh.expects_obj
def translate_po(args):
    conf = fetch_config(args)
    if args.t_translate_config is None:
        tconf = conf.system.files.data.translate
    elif os.path.isfile(args.t_translate_config):
        tconf = TranslateConfig(args.t_translate_config, conf)
    else:
        logger.error(args.t_translate_config + " doesn't exist")
        return

    translate_po_files(args.t_input_file, tconf, args.t_protected_regex)


@argh.arg('--config', '-c', default=None, dest="t_translate_config")
@argh.arg('--input', '-i', required=True, default=None, dest='t_input_file')
@argh.arg('--output', '-o', default=None, dest='t_output_file')
@argh.arg('--protected', '-p', default=None, dest='t_protected_regex')
@argh.named('translate-file')
@argh.expects_obj
def translate_text_doc(args):
    conf = fetch_config(args)
    if args.t_translate_config is None:
        tconf = conf.system.files.data.translate
    elif os.path.isfile(args.t_translate_config):
        tconf = TranslateConfig(args.t_translate_config, conf)
    else:
        logger.error(args.t_translate_config + " doesn't exist")
        return
    translate_file(args.t_input_file, args.t_output_file, tconf, args.t_protected_regex)


@argh.arg('--input', '-i', required=True, default=None, dest='t_input_file')
@argh.arg('--output', '-o', default=None, dest='t_output_file')
@argh.named('flip')
@argh.expects_obj
def flip_text(args):
    if args.t_output_file is None:
        args.t_output_file = args.t_input_file + '.flip'
    flip_text_direction(args.t_input_file, args.t_output_file)


@argh.arg('--po', required=True, default=None, dest='t_input_file')
@argh.named('auto-approve')
@argh.expects_obj
def auto_approve_obvious_po(args):
    auto_approve_po_entries(args.t_input_file)


@argh.arg('--config', '-c', default=None, dest="t_translate_config")
@argh.named('build-model')
@argh.expects_obj
def build_translation_model(args):
    conf = fetch_config(args)
    if args.t_translate_config is None:
        tconf = conf.system.files.data.translate
    elif os.path.isfile(args.t_translate_config):
        tconf = TranslateConfig(args.t_translate_config, conf)
    else:
        logger.error(args.t_translate_config + " doesn't exist")
        return

    if os.path.exists(tconf.paths.project) is False:
        os.makedirs(tconf.paths.project)
    elif os.path.isfile(tconf.paths.project):
        logger.error(tconf.paths.project + " is a file")
        sys.exit(1)
    elif os.listdir(tconf.paths.project) != []:
        logger.error(tconf.paths.project + " must be empty")
        sys.exit(1)

    with open(os.path.join(tconf.paths.project, "translate.yaml"), 'w') as f:
        yaml.dump(tconf.dict(), f, default_flow_style=False)

    tconf.conf.runstate.pool_size = tconf.settings.pool_size
    run_args = get_run_args(tconf)
    app = BuildApp(conf)
    os.environ['IRSTLM'] = tconf.paths.irstlm

    setup_train(tconf)
    setup_tune(tconf)
    setup_test(tconf)

    for idx, parameter_set in enumerate(run_args):
        parameter_set = list(parameter_set)
        parameter_set.append(idx)
        parameter_set.append(tconf)
        t = app.add()
        t.job = build_model
        t.args = parameter_set
        t.description = "model_" + str(parameter_set[9])

    app.run()

    aggregate_model_data(tconf.paths.project)

    from_addr = "build_model@mongodb.com"
    to_addr = [tconf.settings.email]

    with open(tconf.paths.project+"/data.csv") as data:
        msg = MIMEText(data.read())

    msg['Subject'] = "Model Complete"
    msg['From'] = from_addr
    msg['To'] = ", ".join(to_addr)

    server = smtplib.SMTP("localhost")
    server.sendmail(from_addr, to_addr, msg.as_string())
    server.quit()


def get_run_args(tconf):
    return itertools.product(tconf.training_parameters.max_phrase_length,
                             tconf.training_parameters.order,
                             tconf.training_parameters.reordering_language,
                             tconf.training_parameters.reordering_directionality,
                             tconf.training_parameters.score_options,
                             tconf.training_parameters.smoothing,
                             tconf.training_parameters.alignment,
                             tconf.training_parameters.reordering_orientation,
                             tconf.training_parameters.reordering_modeltype)

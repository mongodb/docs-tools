import logging
import argh
import shutil
import os
import sys
import yaml
import itertools

from giza.translate.create_corpora import run_corpora_creation
from giza.translate.build_model import run_build_model, setup_train, setup_tune, setup_test
from giza.translate.model_results import write_model_data
from giza.translate.merge_trans import merge_files
from giza.translate.po_to_corpus import extract_translated_entries
from giza.translate.split_dict import split_dict
from giza.translate.translate_po import translate_po_files
from giza.translate.translate_doc import translate_doc
from giza.serialization import ingest_yaml_doc
from giza.config.helper import fetch_config
from giza.config.corpora import CorporaConfig
from giza.config.translate import TranslateConfig
from giza.app import BuildApp
from giza.command import command
logger = logging.getLogger('giza.operations.translate')

@argh.arg('--config', '-c', default=None, dest="corpora_config")
@argh.named('cc')
def create_corpora(args):
    if args.corpora_config is not None and os.path.exists(args.corpora_config) is False:
        logger.error(args.corpora_config+" doesn't exist")
        sys.exit(1)

    conf = fetch_config(args)
    
    if args.corpora_config is None:
       cconf = conf.system.files.data.corpora
    else: 
        cconf = ingest_yaml_doc(args.corpora_config)

    cconf = CorporaConfig(cconf)
    run_corpora_creation(cconf) 
    
@argh.arg('--config', '-c', default=None, dest="translate_config")
@argh.named('bm')
def build_translation_model(args):
    if args.translate_config is not None and os.path.exists(args.translate_config) is False:
        logger.error(args.translate_config+" doesn't exist")
        sys.exit(1)

    conf = fetch_config(args)

    if args.translate_config is not None and 'translate.yaml' in conf.system.files.paths:
        idx = conf.system.files.paths.index('translate.yaml')
        conf.system.files.paths[idx] = { 'translate': args.translate_config } 

    tconf = conf.system.files.data.translate
    tconf = TranslateConfig(tconf, conf)
     
    if os.listdir(tconf.paths.project) != []:
        logger.error(tconf.paths.project+" must be empty")
        sys.exit(1)
    
    with open(tconf.paths.project+"/translate.yaml", 'w') as f: 
        yaml.dump(tconf.dict(), f, default_flow_style=False)

    tconf.conf.runstate.pool_size = tconf.settings.pool_size
    run_args = get_run_args(tconf) 
    app = BuildApp(conf) 
    os.environ['IRSTLM'] = tconf.paths.irstlm

    setup_train(tconf)
    setup_tune(tconf)
    setup_test(tconf)

    i = 0
    for parameter_set in run_args:
        parameter_set.append(i)
        parameter_set.append(tconf)
        t = app.add()
        t.job = run_build_model
        t.args = parameter_set
        t.description = "model_" + str(parameter_set[9])
        i += 1
    
    app.run()
    write_model_data(tconf.paths.project)
    command('cat {0}/data.csv | mail -s "Output" {1}'.format(tconf.paths.project, tconf.settings.email), capture=True) 
    


def get_run_args(tconf):
    config = itertools.product( tconf.training_parameters.max_phrase_length,
                                tconf.training_parameters.order,
                                tconf.training_parameters.reordering_language,
                                tconf.training_parameters.reordering_directionality,
                                tconf.training_parameters.score_options,
                                tconf.training_parameters.smoothing,
                                tconf.training_parameters.alignment,
                                tconf.training_parameters.reordering_orientation,
                                tconf.training_parameters.reordering_modeltype)
    config = [list(e) for e in config]
    return config

@argh.arg('--config', '-c', default=None, dest="translate_config")
@argh.named('res')
def model_results(args):
    if args.translate_config is not None and os.path.exists(args.translate_config) is False:
        logger.error(args.translate_config+" doesn't exist")
        sys.exit(1)

    conf = fetch_config(args)

    if args.translate_config is not None and 'translate.yaml' in conf.system.files.paths:
        idx = conf.system.files.paths.index('translate.yaml')
        conf.system.files.paths[idx] = { 'translate': args.translate_config } 

    tconf = conf.system.files.data.translate
    tconf = TranslateConfig(tconf, conf)
     
    write_model_data(tconf.paths.project)

@argh.arg('--output', '-o', default=None, dest='output_file')
@argh.arg('--input', '-i', default=None, nargs='*', dest='input_file')
@argh.named('mt')
def merge_translations(args):
    if args.input_file is None:
        logger.error("Please provide input files with --input")
        sys.exit(1)
    if len(args.input_file) > 14:
        logger.error("Too many files, add more annotations and retry")
        sys.exit(1)
    for fn in args.input_file:
        if os.path.exists(fn) is False:
            logger.error(fn+" doesn't exist")
            sys.exit(1)
    
    annotation_list = ['- ', '+ ', '~ ', '> ', '= ','* ', '# ', '$ ', '^ ', '% ', '& ', '@ ']
    merge_files(args.output_file, args.input_file, annotation_list)    
    
@argh.arg('--po', default=None, dest='input_file')
@argh.arg('--source', '-s', default="source_corpus.txt", dest='source')
@argh.arg('--target', '-t', default="target_corpus.txt", dest='target')
@argh.named('p2c')
def po_to_corpus(args):
    if args.input_file is None:
        logger.error("Please provide path to po files with --po")
        sys.exit(1)
    if os.path.exists(args.input_file) is False:
        logger.error(args.input_file+" doesn't exist")
        sys.exit(1)

    extract_translated_entries(args.input_file, args.source, args.target)

@argh.arg('--dict', default=None, dest='input_file')
@argh.arg('--source', '-s', default="source_corpus.txt", dest='source')
@argh.arg('--target', '-t', default="target_corpus.txt", dest='target')
@argh.named('d2c')
def dict_to_corpus(args):
    if args.input_file is None:
        logger.error("Please provide path to dict with --dict")
        sys.exit(1)
    if os.path.exists(args.input_file) is False:
        logger.error(args.input_file+" doesn't exist")
        sys.exit(1)
        
    split_dict(args.input_file, args.source, args.target)

@argh.arg('--config', '-c', default=None, dest="translate_config")
@argh.arg('--po', default=None, dest='input_file')
@argh.arg('--protected', '-p', default=None, dest='protected_regex')
@argh.named('tpo')
def translate_po(args):
    if args.input_file is None:
        logger.error("Please provide path to po files with --po")
        sys.exit(1)
    if os.path.exists(args.input_file) is False:
        logger.error(args.input_file+" doesn't exist")
        sys.exit(1)
    if args.protected_regex is not None and os.path.exists(args.protected_regex) is False:
        logger.error(args.protected_regex+" doesn't exist")
        sys.exit(1)
    if args.translate_config is not None and os.path.exists(args.translate_config) is False:
        logger.error(args.translate_config+" doesn't exist")
        sys.exit(1)

    conf = fetch_config(args)

    if args.translate_config is not None and 'translate.yaml' in conf.system.files.paths:
        idx = conf.system.files.paths.index('translate.yaml')
        conf.system.files.paths[idx] = { 'translate': args.translate_config } 

    tconf = conf.system.files.data.translate
    tconf = TranslateConfig(tconf, conf)

    translate_po_files(args.input_file, tconf ,args.protected_regex)
    
@argh.arg('--config', '-c', default=None, dest="translate_config")
@argh.arg('--source', '-s', default=None, dest='source')
@argh.arg('--target', '-t', default=None, dest='target')
@argh.arg('--protected', '-p', default=None, dest='protected_regex')
@argh.named('tdoc')
def translate_text_doc(args):
    if args.source is None:
        logger.error("Please provide path to file with --source or -s")
        sys.exit(1)
    if os.path.exists(args.source) is False:
        logger.error(args.source+" doesn't exist")
        sys.exit(1)
    if args.protected_regex is not None and os.path.exists(args.protected_regex) is False:
        logger.error(args.protected_regex+" doesn't exist")
        sys.exit(1)
    if args.translate_config is not None and os.path.exists(args.translate_config) is False:
        logger.error(args.translate_config+" doesn't exist")
        sys.exit(1)

    conf = fetch_config(args)

    if args.translate_config is not None and 'translate.yaml' in conf.system.files.paths:
        idx = conf.system.files.paths.index('translate.yaml')
        conf.system.files.paths[idx] = { 'translate': args.translate_config } 

    tconf = conf.system.files.data.translate
    tconf = TranslateConfig(tconf, conf)

    translate_doc(args.source, tconf, args.target, args.protected_regex)



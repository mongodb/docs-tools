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

import os
import time
import datetime
import logging
import json

from giza.translate.utils import Timer, set_logger, pcommand

'''
This module builds the translation model by training, tuning, and then testing.
It also binarizes the model at the end so that it's faster to load the decoder
later on. Using a config file as shown in the translate.yaml, you can customize
the build and what settings it uses to experiment. It will run all of the
different combinations of parameters that you give it in parallel
Best to run this with as many threads as possible or else it will take a really
long time.
'''

logger = logging.getLogger("giza.translate.model")


def tokenize_corpus(corpus_dir, corpus_name, tconf):
    '''This function tokenizes a corpus
    :param string corpus_dir: path to directory to the corpus
    :param string corpus_name: name of the corpus in the directory
    :param config tconf: translate configuration
    '''

    cmd = "{0}/scripts/tokenizer/tokenizer.perl -l en < {1}/{3}.{4} > {2}/{3}.tok.{4} -threads {5}"
    pcommand(cmd.format(tconf.paths.moses, corpus_dir, tconf.paths.aux_corpus_files, corpus_name, "en", tconf.settings.threads))
    pcommand(cmd.format(tconf.paths.moses, corpus_dir, tconf.paths.aux_corpus_files, corpus_name, tconf.settings.foreign, tconf.settings.threads))


def train_truecaser(corpus_name, tconf):
    '''This function trains the truecaser on a corpus
    :param string corpus_name: name of the corpus in the directory
    :param config tconf: translate configuration
    '''
    cmd = "{0}/scripts/recaser/train-truecaser.perl --model {1}/truecase-model.{3} --corpus {1}/{2}.tok.{3}"
    pcommand(cmd.format(tconf.paths.moses, tconf.paths.aux_corpus_files, corpus_name, "en"))
    pcommand(cmd.format(tconf.paths.moses, tconf.paths.aux_corpus_files, corpus_name, tconf.settings.foreign))


def truecase_corpus(corpus_name, tconf):
    '''This function truecases a corpus
    :param string corpus_name: name of the corpus in the directory
    :param config tconf: translate configuration
    '''
    cmd = "{0}/scripts/recaser/truecase.perl --model {1}/truecase-model.{3} < {1}/{2}.tok.{3} > {1}/{2}.true.{3}"
    pcommand(cmd.format(tconf.paths.moses, tconf.paths.aux_corpus_files, corpus_name, "en"))
    pcommand(cmd.format(tconf.paths.moses, tconf.paths.aux_corpus_files, corpus_name, tconf.settings.foreign))


def clean_corpus(corpus_name, tconf):
    '''This function cleans a corpus to have proper length up to 80 words
    :param string corpus_name: name of the corpus in the directory
    :param config tconf: translate configuration
    '''
    pcommand("{0}/scripts/training/clean-corpus-n.perl {1}/{2}.true {3} en {1}/{2}.clean 1 80".format(tconf.paths.moses, tconf.paths.aux_corpus_files, corpus_name, tconf.settings.foreign))


def setup_train(tconf):
    '''This function sets up the training corpus
    :param config tconf: translate configuration
    '''
    tokenize_corpus(tconf.train.dir, tconf.train.name, tconf)
    train_truecaser(tconf.train.name, tconf)
    truecase_corpus(tconf.train.name, tconf)
    clean_corpus(tconf.train.name, tconf)


def setup_tune(tconf):
    '''This function sets up the tuning corpus
    :param config tconf: translate configuration
    '''
    tokenize_corpus(tconf.tune.dir, tconf.tune.name, tconf)
    truecase_corpus(tconf.tune.name, tconf)


def setup_test(tconf):
    '''This function sets up the testing corpus
    :param config tconf: translate configuration
    '''
    tokenize_corpus(tconf.test.dir, tconf.test.name, tconf)
    truecase_corpus(tconf.test.name, tconf)


def lm(lm_path,
       l_order,
       l_smoothing,
       tconf,
       d):
    '''This function builds the language model for the goven config
    :param string lm_path: path to language model directory
    :param int l_order: n-gram order
    :param string l_smoothing: smoothing algorithm
    :param config tconf: translate configuration
    :param dict d: output dictionary
    '''

    # Create language model
    with Timer(d, 'lm'):
        os.makedirs(lm_path)
        pcommand("{0}/bin/add-start-end.sh < {1}/{2}.true.{3} > {4}/{2}.sb.{3}".format(tconf.paths.irstlm, tconf.paths.aux_corpus_files, tconf.train.name, tconf.settings.foreign, lm_path))
        pcommand("{0}/bin/build-lm.sh -i {5}/{1}.sb.{4} -t {5}/tmp -p -n {2} -s {3} -o {5}/{1}.ilm.{4}.gz".format(tconf.paths.irstlm, tconf.train.name, l_order, l_smoothing, tconf.settings.foreign, lm_path))
        pcommand("{0}/bin/compile-lm --text  {3}/{1}.ilm.{2}.gz {3}/{1}.arpa.{2}".format(tconf.paths.irstlm, tconf.train.name, tconf.settings.foreign, lm_path))
        pcommand("{0}/bin/build_binary -i {3}/{1}.arpa.{2} {3}/{1}.blm.{2}".format(tconf.paths.moses, tconf.train.name, tconf.settings.foreign, lm_path))
        pcommand("echo 'Is this a Spanish sentance?' | {0}/bin/query {1}/{2}.blm.{3}".format(tconf.paths.moses, lm_path, tconf.train.name, tconf.settings.foreign))


def train(working_path,
          lm_path,
          l_len,
          l_order,
          l_lang,
          l_direct,
          l_score,
          l_align,
          l_orient,
          l_model,
          tconf,
          d):
    '''This function does the training for the given configuration
    :param string working_path: path to working directory
    :param int l_len: max phrase length
    :param int l_order: n-gram order
    :param string l_lang: reordering language setting, either f or fe
    :param string l_direct: reordering directionality setting, either forward, backward, or bidirectional
    :param string l_score: score options setting, any combination of --GoodTuring, --NoLex, --OnlyDirect
    :param string l_align: alignment algorithm
    :param string l_orient: reordering orientation setting, either mslr, msd, monotonicity, leftright
    :param string l_model: reordering modeltype setting, either wbe, phrase, or hier
    :param config tconf: translate configuration
    :param dict d: output dictionary
    '''

    with Timer(d, 'train'):
        os.makedirs(working_path)
        pcommand("{0}/scripts/training/train-model.perl -root-dir {13}/train -corpus {1}/{2}.clean -f en -e {3} --score-options \'{4}\' -alignment {5} -reordering {6}-{7}-{8}-{9} -lm 0:{10}:{11}/{2}.blm.{3}:1 -mgiza -mgiza-cpus {12} -external-bin-dir {0}/tools -cores {12} --parallel --parts 3 2>&1 > {13}/training.out".format(tconf.paths.moses, tconf.paths.aux_corpus_files, tconf.train.name, tconf.settings.foreign, l_score, l_align, l_model, l_orient, l_direct, l_lang, l_order, lm_path, tconf.settings.threads, working_path))


def tune(working_path,
         tconf,
         d):
    '''This function tunes the model made so far.
    :param string working_path: path to working directory
    :param config tconf: translate configuration
    :param dict d: output dictionary
    '''
    with Timer(d, 'tune'):
        pcommand("{0}/scripts/training/mert-moses.pl {1}/{2}.true.en {1}/{2}.true.{3} {0}/bin/moses  {4}/train/model/moses.ini --working-dir {4}/mert-work --mertdir {0}/bin/ 2>&1 > {4}/mert.out".format(tconf.paths.moses, tconf.paths.aux_corpus_files, tconf.tune.name, tconf.settings.foreign, working_path))


def binarise(working_path,
             l_lang,
             l_direct,
             l_orient,
             l_model,
             tconf,
             d):
    '''This function binarises the phrase and reoridering tables.
    Binarising them speeds up loading the decoder, though doesn't actually speed up decoding sentences
    :param string working_path: the path to the working directory
    :param string l_lang: reordering language setting, either f or fe
    :param string l_direct: reordering directionality setting, either forward, backward, or bidirectional
    :param string l_orient: reordering orientation setting, either mslr, msd, monotonicity, leftright
    :param string l_model: reordering modeltype setting, either wbe, phrase, or hier
    :param config tconf: translate configuration
    :param dict d: output dictionary
    '''

    with Timer(d, 'binarise'):
        pcommand("mkdir -p {0}/binarised-model".format(working_path))
        pcommand("{0}/bin/processPhraseTable  -ttable 0 0 {1}/train/model/{2}.gz -nscores 5 -out {1}/binarised-model/phrase-table".format(tconf.paths.moses, working_path, tconf.settings.phrase_table_name))
        pcommand("{0}/bin/processLexicalTable -in {1}/train/model/{6}.{2}-{3}-{4}-{5}.gz -out {1}/binarised-model/reordering-table".format(tconf.paths.moses, working_path, l_model, l_orient, l_direct, l_lang, tconf.settings.reordering_name))
        pcommand("cp {0}/mert-work/moses.ini {0}/binarised-model".format(working_path))
        pcommand("sed -i 's/PhraseDictionaryMemory/PhraseDictionaryBinary/' {0}/binarised-model/moses.ini".format(working_path))
        pcommand("sed -i 's/train\/model\/{1}.gz/binarised-model\/phrase-table/' {0}/binarised-model/moses.ini".format(working_path, tconf.settings.phrase_table_name))


def test_filtered(working_path,
                  tconf,
                  d):
    '''This function tests the model made so far.
    It first filters the data to only use those needed for the test file.
    This can speed it  up over the binarised version but has a history of failing on certain corpora
    :param string working_path: path to working directory
    :param config tconf: translate configuration
    :param dict d: output dictionary

    '''
    with Timer(d, 'test'):
        pcommand("{0}/scripts/training/filter-model-given-input.pl {3}/filtered {3}/mert-work/moses.ini {2}/{1}.true.en -Binarizer {0}/bin/processPhraseTable".format(tconf.paths.moses, tconf.test.name, tconf.paths.aux_corpus_files, working_path))
        pcommand("{0}/bin/moses -f {1}/filtered/moses.ini  < {2}/{3}.true.en > {1}/{3}.translated.{4} 2> {1}/{3}.out".format(tconf.paths.moses, working_path, tconf.paths.aux_corpus_files, tconf.test.name, tconf.settings.foreign))
        c = pcommand("{0}/scripts/generic/multi-bleu.perl -lc {1}/{2}.true.{4} < {3}/{2}.translated.{4}".format(tconf.paths.moses, tconf.paths.aux_corpus_files, tconf.test.name, working_path, tconf.settings.foreign))
        d["BLEU"] = c.out


def test_binarised(working_path,
                   tconf,
                   d):
    '''This function tests the model so far with the binarised phrase table
    :param string working_path: path to working directory
    :param config tconf: translate configuration
    :param dict d: output dictionary

    '''
    with Timer(d, 'test'):
        pcommand("{0}/bin/moses -f {1}/binarised-model/moses.ini  < {2}/{3}.true.en > {1}/{3}.translated.{4} 2> {1}/{3}.out".format(tconf.paths.moses, working_path, tconf.paths.aux_corpus_files, tconf.test.name, tconf.settings.foreign))
        c = pcommand("{0}/scripts/generic/multi-bleu.perl -lc {1}/{2}.true.{4} < {3}/{2}.translated.{4}".format(tconf.paths.moses, tconf.paths.aux_corpus_files, tconf.test.name, working_path, tconf.settings.foreign))
        d["BLEU"] = c.out


def build_model(l_len,
                l_order,
                l_lang,
                l_direct,
                l_score,
                l_smoothing,
                l_align,
                l_orient,
                l_model,
                i,
                tconf):
    '''This function runs one configuration of the training script.
    This function can be called with different arguments to run multiple configurations in parallel
    :param int l_len: max phrase length
    :param int l_order: n-gram order
    :param string l_lang: reordering language setting, either f or fe
    :param string l_direct: reordering directionality setting, either forward, backward, or bidirectional
    :param string l_score: score options setting, any combination of --GoodTuring, --NoLex, --OnlyDirect
    :param string l_smoothing: smoothing algorithm
    :param string l_align: alignment algorithm
    :param string l_orient: reordering orientation setting, either mslr, msd, monotonicity, leftright
    :param string l_model: reordering modeltype setting, either wbe, phrase, or hier
    :param int i: configuration number, should be unique for each
    :param config tconf: translate configuration
    '''

    set_logger(logger, "Process "+str(i))
    run_start = time.time()
    lm_path = "{0}/{1}/lm".format(tconf.paths.project, i)
    working_path = "{0}/{1}/working".format(tconf.paths.project, i)

    os.makedirs("{0}/{1}".format(tconf.paths.project, i))

    # Logs information about the current configuation
    d = {"i": i,
         "start_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
         "order": l_order,
         "smoothing": l_smoothing,
         "score_options": l_score,
         "alignment": l_align,
         "reordering_modeltype": l_model,
         "reordering_orientation": l_orient,
         "reordering_directionality": l_direct,
         "reordering_language": l_lang,
         "max_phrase_length": l_len}

    lm(lm_path, l_order, l_smoothing, tconf, d)
    train(working_path, lm_path, l_len, l_order, l_lang, l_direct, l_score, l_align, l_orient, l_model, tconf, d)
    tune(working_path, tconf, d)
    binarise(working_path, l_lang, l_direct, l_orient, l_model, tconf, d)
    test_binarised(working_path, tconf, d)

    d["run_time_hms"] = str(datetime.timedelta(seconds=(time.time()-run_start)))
    d["end_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    with open("{0}/{1}/{1}.json".format(tconf.paths.project, i), "w", 1) as ilog:
        json.dump(d, ilog, indent=4, separators=(',', ': '))

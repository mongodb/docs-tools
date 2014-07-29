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

import sys
from  giza.translate.build_model import pcommand
import logging
import tempfile
import shutil
import os

'''
This module translates any text file according the parameters in a config file
'''
logger = logging.getLogger('giza.translate.translate_doc')

class TempDir():
    ''' This class creates a temporary folder in which to put temporary files.
    It removes them automatically upon leaving the context
    '''
    def __init__(self, suffix='', prefix='tmp', dir=None, super_temp=None):
        ''' This constructs the TempDir object
        :param string suffix: the string gets added to the end of the temp directory
        :param string prefix: the string gets added to the beginning of the temp directory
        :param string dir: a directory in which to put the temporary directory in
        :param string super_temp: If you have a TempDir context inside of a TempDir context, this allows you to not create two. Just pass in the directory of the previous temporary directory
        '''
        self.suffix = suffix
        self.prefix = prefix
        self.dir = dir
        self.super_temp = super_temp

    def __enter__(self):
        if self.super_temp is not None:
            return self.super_temp
        self.temp_dir = tempfile.mkdtemp(self.suffix, self.prefix, self.dir)
        return self.temp_dir

    def __exit__(self, *args):
        if self.super_temp is None:
            shutil.rmtree(self.temp_dir, ignore_errors=True)



def decode(in_file, out_file,  tconf, protected_file, super_temp=None):
    '''This function translates a given file to another file
    :param string in_file: path to file to be translated 
    :param string out_file: path to file where translated output should be written 
    :param config tconf: translateconfig object 
    :param string protected_file': path to regex file to protect expressions from tokenization
    :param string super_temp: If you have a TempDir context inside of a TempDir context, this allows you to not create two. Just pass in the directory of the previous temporary directory
    '''
    with TempDir(super_temp=super_temp) as temp:
        logger.info("tempdir: "+temp)
        logger.info("decoding: "+in_file)
        if super_temp is None:
            shutil.copy(in_file, temp)
        in_file = os.path.basename(in_file)
        if protected_file is not None:
            pcommand("{0}/scripts/tokenizer/tokenizer.perl -l en < {4}/{1} > {4}/{1}.tok.en -threads {2} -protected {3}".format(tconf.paths.moses, in_file, tconf.settings.threads, protected_file, temp))
        else:
            pcommand("{0}/scripts/tokenizer/tokenizer.perl -l en < {3}/{1} > {3}/{1}.tok.en -threads {2}".format(tconf.paths.moses, in_file, tconf.settings.threads, temp))
        pcommand("{0}/scripts/recaser/truecase.perl --model {1}/truecase-model.en < {3}/{2}.tok.en > {3}/{2}.true.en".format(tconf.paths.moses, tconf.paths.aux_corpus_files, in_file, temp))
        pcommand("{0}/bin/moses -f {1}/{3}/working/binarised-model/moses.ini < {4}/{2}.true.en > {4}/{2}.true.trans".format(tconf.paths.moses, tconf.paths.project, in_file, tconf.settings.best_run, temp))
        pcommand("{0}/scripts/recaser/detruecase.perl < {2}/{1}.true.trans > {2}/{1}.tok.trans".format(tconf.paths.moses, in_file, temp))
        pcommand("{0}/scripts/tokenizer/detokenizer.perl -l en < {3}/{1}.tok.trans > {2}".format(tconf.paths.moses, in_file, out_file, temp))
 
def translate_doc(in_fn, tconf, out_fn=None, protected_file=None):
    '''This function translates the file
    :param string in_fn: path to file to be translated 
    :param config tconf: translateconfig object
    '''
    if out_fn is None: out_fn = in_fn + ".translated"
    decode(in_fn, out_fn, tconf, protected_file)
    return out_fn
    
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
import logging
import time
import datetime

from giza.command import command

'''
This module prints out all files line by line to compare lines
Just give it as many files as you want at the start, it'll finish when the first file is empty if they are not the same amount of lines
It takes in a list of annotations that it uses to more visually see what the different lines are.
'''
logger = logging.getLogger('giza.translate.utils')

def get_file_list(path, input_extension):
    ''' This function wraps around expand tree to return a list of only 1 file 
    if the user gives a path to a file and not a directory
    :param string path: path to the file
    :param list input_extension: a list (or a single) of extensions that is acceptable
    '''
    if os.path.isfile(path):
        if input_extension != None:
            if isinstance(input_extension, list):
                if os.path.splitext(path)[1][1:] not in input_extension:
                    return []
            else:
                if not path.endswith(input_extension):
                    return []
        return [path]
    return expand_tree(path, input_extension)

def setLogger(logger, logger_id):
    '''This method sets the formatter to the logger to have a custom field called the logger_id
    :param logger logger: The logger for the module
    :param string logger_id: the identifier for the instance of the module
    '''
    for handler in logger.handlers:
        logger.removeHandler(handler)
    f = logging.Formatter("%(levelname)s|%(asctime)s|%(name)s|{0}: %(message)s".format(logger_id))
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(f)
    logger.addHandler(h)
    logger.propagate = False


class Timer(object):
    '''This class is responsible for timing the processes and then both logging them and saving them
    to the process's dictionary object
    '''
    def __init__(self, d, name=None):
        self.d = d
        if name is None:
            self.name = 'task'
        else:
            self.name = name

    def __enter__(self):
        self.start = time.time()
        time_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        self.d[self.name+"_start_time"] = time_now 
        message = '[timer]: {0} started at {1}'
        message = message.format(self.name, time_now)
        logger.info(message)

    def __exit__(self, *args):
        total_time = time.time()-self.start
        message = '[timer]: time elapsed for {0} was: {1}'
        message = message.format(self.name, str(datetime.timedelta(seconds=total_time)))
        logger.info(message)
        self.d[self.name+"_time"] = total_time
        self.d[self.name+"_time_hms"] = str(datetime.timedelta(seconds=total_time))

def pcommand(c):
    '''This function wraps the command module with logging functionality
    :param string c: command to run and log
    :returns: a command result object
    '''
    
    logger.info(c)
    o = command(c, capture=True)
    if len(o.out) != 0:
        logger.info(o.out)
    if len(o.err) != 0:
        logger.info(o.err)
    return o

def merge_files(output_file, input_files, annotation_list):
    '''This function merges all of the files in the file_list into the output file
    annotations are made in order to help differentiate which line is from which file
    :param string output_file: The file path to output the lines to, if None goes to stdout
    :param list input_files: The list of file names to merge
    :param list annotation_list: The list of annotations to use (*,-,+,~...etc.)
    '''
    
    if len(input_files) > len(annotation_list):
        logger.error("Too many files, add more annotations and retry")
        sys.exit(1)
    
    for fn in input_files:
        if os.path.exists(fn) is False:
            logger.error(fn+" doesn't exist")
            sys.exit(1)

    if output_file is None:
        out = sys.stdout
    else:
        out = open(output_file, 'w', 1)
    open_files = []
    for file in input_files:
        open_files.append(open(file,"r"))
    t = True
    while t:
        for index, file in enumerate(open_files):
            line = file.readline()
            if not line:
                t = False
                break
            if line[-1] == '\n': out.write(annotation_list[index]+line)    
            else: out.write(annotation_list[index]+line+'\n')    
        out.write("\n")
    for file in open_files:
        file.close()
    out.close()

class TempDir(object):
    ''' This class creates a temporary folder in which to put temporary files.
    It removes them automatically upon leaving the context
    '''
    def __init__(self, dir=None, super_temp=None):
        ''' This constructs the TempDir object
        :param string suffix: the string gets added to the end of the temp directory
        :param string prefix: the string gets added to the beginning of the temp directory
        :param string dir: a directory in which to put the temporary directory in
        :param string super_temp: If you have a TempDir context inside of a TempDir context, this allows you to not create two. Just pass in the directory of the previous temporary directory
        '''
        self.dir = dir
        self.super_temp = super_temp

    def __enter__(self):
        if self.super_temp is not None:
            return self.super_temp
        self.temp_dir = tempfile.mkdtemp(dir=self.dir)
        return self.temp_dir

    def __exit__(self, *args):
        if self.super_temp is None:
            shutil.rmtree(self.temp_dir, ignore_errors=True)


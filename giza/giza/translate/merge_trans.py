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

'''
This module prints out all files line by line to compare lines
Just give it as many files as you want at the start, it'll finish when the first file is empty if they are not the same amount of lines
It takes in a list of annotations that it uses to more visually see what the different lines are.
'''
logger = logging.getLogger('giza.translate.merge_trans')

def merge_files(output_file, input_files, annotation_list):
    '''This function merges all of the files in the file_list into the output file
    annotations are made in order to help differentiate which line is from which file
    :param string output_file: The file path to output the lines to, if None goes to stdout
    :param list input_files: The list of file names to merge
    :param list annotation_list: The list of annotations to use (*,-,+,~...etc.)
    '''
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

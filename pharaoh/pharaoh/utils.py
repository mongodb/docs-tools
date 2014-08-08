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

from bson import json_util
import os
import logging

logger = logging.getLogger('pharaoh.utils')

def load_json(file_name, db):
    file_no_ext = os.path.basename(file_name)
    file_no_ext = os.path.splitext(file_no_ext)[0]
    with open(file_name,"r") as file:
        json_data = file.read()
        data = json.loads(json_data, object_hook=json_util.object_hook)
        for d in data[file_no_ext]:
            db[file_no_ext].insert(d)


def get_file_list(path, input_extension=['po', 'pot']):
    file_list = []
    if os.path.isfile(path):
        return [path]
    else:
        for root, sub_folders, files in os.walk(path):
            for file in files:
                if file.startswith('.#'):
                    continue
                elif file.endswith('swp'):
                    continue
                else:
                    f = os.path.join(root, file)
                    if input_extension is not None:
                        if isinstance(input_extension, list):
                            if os.path.splitext(f)[1][1:] not in input_extension:
                                continue
                        else:
                            if not f.endswith(input_extension):
                                continue

                    file_list.append(f)

    return file_list

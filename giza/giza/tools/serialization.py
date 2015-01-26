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
import yaml
import logging

logger = logging.getLogger("giza.tools.serialization")

from giza.tools.files import InvalidFile

def ingest_yaml_list(*filenames):
    o = []

    for fn in filenames:
        if isinstance(fn, list):
            filenames.extend(fn)
            continue

        data = ingest_yaml(fn)

        if isinstance(data, list):
            o.extend(data)
        else:
            o.append(data)

    return o

def ingest_yaml_doc(filename, force=False):
    data = ingest_yaml_list(filename)

    if force is True or len(data) == 1:
        return data[0]
    else:
        if len(data) == 0:
            return {}
        elif len(data) > 1:
            raise Exception('{0} has more than one document.'.format(filename))
        else:
            return data[0]

def ingest_yaml(filename):
    o = []
    with open(filename, 'r') as f:
        try:
            data = yaml.load_all(f)
        except:
            logger.error("error decoding yaml in: " + filename)
            raise InvalidFile(filename)

        o.extend(data)

    if len(o) == 1:
        o = o[0]

    return o

def write_yaml(input, filename):
    with open(filename, 'w') as f:
        if isinstance(input, list):
            f.write(yaml.safe_dump_all(input, default_flow_style=False))
        elif isinstance(input, dict):
            f.write(yaml.safe_dump(input, default_flow_style=False))
        else:
            raise Exception('cannot dump $s objects to yaml.' % str(type(input)))

        f.write('...\n')

def write_json(input, filename):
    with open(filename, 'w') as f:
        if isinstance(input, (dict, list)):
            json.dump(input, f, indent=3, sort_keys=True)
        else:
            raise Exception('cannot dump $s objects to json.' % str(type(input)))


def dict_from_list(key, source):
    return dict( (item[key], item) for item in source )

def ingest_json(filename):
    with open(filename, 'r') as f:
        try:
            o = json.load(f)
        except:
            o = [ json.loads(doc)
                  for doc in f.readlines() ]

    if isinstance(o, list) and len(o) == 1:
        o = o[0]

    return o

def ingest_json_doc(filename):
    return ingest_json(filename)

def ingest_json_list(filename):
    o = ingest_json(filename)

    if isinstance(o, list):
        return o
    else:
        return [o]

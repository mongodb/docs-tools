import json

import yaml

def ingest_yaml_list(filename):
    o = ingest_yaml(filename)

    if isinstance(o, list):
        return o
    else:
        return [o]

def ingest_yaml_doc(filename, force=False):
    data = ingest_yaml_list(filename)

    if force is True or len(data) == 1:
        return data[0]
    else:
        if len(data) > 1:
            raise Exception('{0} has more than one document.'.format(filename))
        else:
            return data[0]

def ingest_yaml(filename):
    o = []
    with open(filename, 'r') as f:
        data = yaml.load_all(f)

        for i in data:
            o.append(i)

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

def ingest_json(filename):
    o = []
    with open(filename, 'r') as f:
        for doc in f.readlines():
            o.append(json.loads(doc))

    if len(o) == 1:
        o = o[0]

    return o

def ingest_json_list(filename):
    o = ingest_json(filename)

    if isinstance(o, list):
        return o
    else:
        return [o]

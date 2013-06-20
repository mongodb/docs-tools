import re
import yaml
import sys
import os
import subprocess
import json
import hashlib

class AttributeDict(dict):
    def __init__(self, value=None):
        if value is None:
            pass
        elif isinstance(value, dict):
            for key in value:
                self.__setitem__(key, value[key])
        else:
            raise TypeError('expected dict')

    def __setitem__(self, key, value):
        if isinstance(value, dict) and not isinstance(value, AttributeDict):
            value = AttributeDict(value)
        dict.__setitem__(self, key, value)

    def __getitem__(self, key):
        NotFound = object()
        found = self.get(key, NotFound)
        if found is NotFound:
            err = 'key named "{0}" does not exist.'.format(key)
            raise AttributeError(err)
        else:
            return found

    __setattr__ = __setitem__
    __getattr__ = __getitem__

class BuildConfiguration(AttributeDict):
    def __init__(self, filename, directory=None):
        if directory is None:
            directory = os.path.split(os.path.abspath(filename))[0]
        conf = ingest_yaml_doc(get_conf_file(filename, directory))

        for key, value in conf.items():
            if isinstance(value, (list, tuple)):
                for item in value:
                    if isinstance(item, dict):
                        setattr(self, key, AttributeDict(item))
                    else:
                        setattr(self, key, value)
            else:
                if isinstance(value, dict):
                    setattr(self, key, AttributeDict(value))
                else:
                    setattr(self, key, value)


def md5_file(file, block_size=2**20):
    md5 = hashlib.md5()

    with open(file, 'rb') as f:
        for chunk in iter(lambda: f.read(128*md5.block_size), b''):
            md5.update(chunk)

    return md5.hexdigest()

def log_command_output(cmd, path, logfile, wait=False):
    with open(logfile, 'a') as f:
        p = subprocess.Popen(cmd, cwd=path, stdout=f, stderr=f)
        if wait is True:
            p.wait()

def shell_value(args, path=None):
    if path is None:
        path = os.getcwd()

    if isinstance(args , str):
        r = re.compile("\s+")
        args = r.split(args)

    p = subprocess.Popen(args, cwd=path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    r = p.communicate()

    return str(r[0].decode().rstrip())

def get_commit(path=None):
    if path is None:
        path = os.getcwd()

    return shell_value('git rev-parse --verify HEAD', path)

def get_branch(path=None):
    if path is None:
        path = os.getcwd()

    return shell_value('git symbolic-ref HEAD', path).split('/')[2]

def _expand_tree(path, input_extension):
    file_list = []

    for root, subFolders, files in os.walk(path):
        for file in files:
            f = os.path.join(root, file)

            try:
                if f.rsplit('.', 1)[1] == input_extension:
                    file_list.append(f)
            except IndexError:
                continue

    return file_list

def expand_tree(path, input_extension='yaml'):
    ret = []

    if isinstance(input_extension, list):
        for ext in input_extension:
            ret.extend(_expand_tree(path, input_extension))
    else:
        ret.extend(_expand_tree(path, input_extension))

    return ret

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

def get_conf_file(file, directory=None):
    if directory is None:
        from docs_meta import conf
        directory = conf.build.paths.builddata

    conf_file = os.path.split(file)[1].rsplit('.', 1)[0] + '.yaml'

    return os.path.join(directory, conf_file)

def build_platform_notification(title, content):
    if sys.platform.startswith('darwin'):
        return 'growlnotify -n "mongodb-doc-build" -a "Terminal.app" -m %s -t %s' % (title, content)
    if sys.platform.startswith('linux'):
        return 'notify-send "%s" "%s"' % (title, content)

def symlink(name, target):
    if not os.path.islink(name):
        try:
            os.symlink(target, name)
        except AttributeError:
            from win32file import CreateSymbolicLink
            CreateSymbolicLink()
        except ImportError:
            exit('ERROR: platform does not contain support for symlinks. Windows users need to pywin32.')

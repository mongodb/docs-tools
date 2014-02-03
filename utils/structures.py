import json
import yaml
import os.path

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
        if '-' in key:
            key = key.replace('-', '_')

        if isinstance(value, dict) and not isinstance(value, AttributeDict):
            value = AttributeDict(value)
        dict.__setitem__(self, key, value)

    def __getitem__(self, key):
        if '-' in key:
            key = key.replace('-', '_')

        NotFound = object()
        found = self.get(key, NotFound)
        if found is NotFound:
            err = 'key named "{0}" does not exist.'.format(key)
            raise AttributeError(err)
        else:
            return found

    def __contains__(self, key):
        if '-' in key:
            key = key.replace('-', '_')

        try:
            return self.has_key(key)
        except AttributeError:
            return key in self.keys()

    __setattr__ = __setitem__
    __getattr__ = __getitem__

class BuildConfiguration(AttributeDict):
    def __init__(self, filename, directory=None):
        if directory is None:
            directory = os.path.split(os.path.abspath(filename))[0]

        file_path = os.path.join(directory, filename)

        if filename.endswith('yaml'):
            with open(file_path, 'r') as f:
                conf = yaml.load(f)
        elif filename.endswith('json'):
            with open(file_Path, 'r') as f:
                conf = json.load(f)

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

def conf_from_list(key, source):
    return AttributeDict(dict( (item[key], item) for item in source ))

def get_conf_file(file, directory=None):
    if directory is None:
        from docs_meta import get_conf
        conf = get_conf()

        directory = conf.paths.builddata

    conf_file = os.path.split(file)[1].rsplit('.', 1)[0] + '.yaml'

    return os.path.join(directory, conf_file)

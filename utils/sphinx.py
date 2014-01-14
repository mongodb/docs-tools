import os.path

from utils.config import lazy_conf
from utils.serialization import ingest_yaml

def get_sphinx_builders(conf=None):
    conf = lazy_conf(conf)

    path = os.path.join(conf.paths.builddata, 'sphinx.yaml')

    sconf = ingest_yaml(path)

    if 'builders' in sconf:
        return sconf['builders']
    else:
        for i in ['prerequisites', 'generated-source']:
            if i in sconf:
                del sconf[i]
        return sconf.keys()

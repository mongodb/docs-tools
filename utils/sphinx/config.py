import os.path
import pkg_resources
import logging

logger = logging.getLogger(os.path.basename(__file__))

from multiprocessing import cpu_count
from copy import deepcopy

from utils.structures import BuildConfiguration, AttributeDict
from utils.config import render_sphinx_config

def get_sconf(conf):
    return BuildConfiguration(filename='sphinx.yaml',
                              directory=os.path.join(conf.paths.projectroot,
                                                     conf.paths.builddata))

def is_parallel_sphinx(version):
    return version >= '1.2'

def get_sphinx_args(sconf, conf):
    o = []

    o.append(get_tags(sconf.builder, sconf))
    o.append('-q')

    o.append('-b {0}'.format(sconf[sconf.builder].builder))

    if (is_parallel_sphinx(pkg_resources.get_distribution("sphinx").version) and
        'editions' not in sconf):
        o.append(' '.join( [ '-j', str(cpu_count() + 1) ]))

    o.append(' '.join( [ '-c', conf.paths.projectroot ] ))

    if 'language' in sconf[sconf.builder]:
        o.append("-D language='{0}'".format(sconf[sconf.builder].language))

    return ' '.join(o)

def compute_sphinx_config(builder, sconf, conf):
    # vestigial. most of the logic of this function was moved into
    # utils.config.render_sphinx_config

    computed_config = deepcopy(sconf)

    if 'editions' in sconf:
        computed_config.builder = builder.split('-')[0]
        if 'edition' not in computed_config:
            raise Exception('[sphinx] [error]: builds with editions must specify an edition.')
    else:
        computed_config.edition = None

    if 'builder' not in computed_config:
        computed_config['builder'] = builder

    return computed_config

def get_tags(target, sconf):
    ret = set()

    ret.add(target)
    ret.add(target.split('-')[0])

    if target.startswith('html') or target.startswith('dirhtml'):
        ret.add('website')
    else:
        ret.add('print')

    if 'edition' in sconf:
        ret.add(sconf.edition)

    return ' '.join([' '.join(['-t', i ])
                     for i in ret
                     if i is not None])

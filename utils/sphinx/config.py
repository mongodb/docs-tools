import os.path
import pkg_resources
import logging

logger = logging.getLogger(os.path.basename(__file__))

from multiprocessing import cpu_count
from copy import deepcopy

from utils.structures import AttributeDict
from utils.serialization import ingest_yaml_doc
from utils.config import render_sphinx_config

def get_sconf(conf):
    return ingest_yaml_doc(os.path.join(conf.paths.projectroot,
                                        conf.paths.builddata, 'sphinx.yaml'))

def is_parallel_sphinx(version):
    return version >= '1.2'

def get_sphinx_args(sconf, conf):
    o = []

    o.append(get_tags(sconf.builder, sconf))
    o.append('-q')

    o.append('-b {0}'.format(sconf.builder))

    if (is_parallel_sphinx(pkg_resources.get_distribution("sphinx").version) and
        'editions' not in sconf):
        o.append(' '.join( [ '-j', str(cpu_count() + 1) ]))

    o.append(' '.join( [ '-c', conf.paths.projectroot ] ))

    if 'language' in sconf:
        o.append("-D language='{0}'".format(sconf.language))

    return ' '.join(o)

def compute_sphinx_config(builder, sconf, conf):
    # vestigial. most of the logic of this function was moved into
    # utils.config.render_sphinx_config

    computed_config = deepcopy(sconf)

    if 'editions' in sconf:
        if 'builder' not in computed_config:
            sp_builder = builder.split('-')[0]
            logger.debug('set builder for {0} to {1}'.format(builder, sp_builder))
            computed_config[builder]['builder'] = sp_builder

        logger.debug(computed_config[builder])

        if 'edition' not in computed_config[builder]:
            logger.critical('[sphinx] [error]: builds with editions must specify an edition.')
    else:
        computed_config['edition'] = None

    return AttributeDict(computed_config[builder])

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

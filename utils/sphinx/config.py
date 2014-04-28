import os.path
import pkg_resources

from multiprocessing import cpu_count
from copy import deepcopy

from utils.structures import BuildConfiguration

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
    o.append('-b {0}'.format(sconf.builder))

    if (is_parallel_sphinx(pkg_resources.get_distribution("sphinx").version) and
        'editions' not in sconf):
        o.append(' '.join( [ '-j', str(cpu_count() + 1) ]))

    o.append(' '.join( [ '-c', conf.paths.projectroot ] ))

    if 'language' in sconf:
        o.append("-D language='{0}'".format(sconf.language))

    return ' '.join(o)

def compute_sphinx_config(builder, sconf, conf):
    if 'inherit' in sconf[builder]:
        computed_config = deepcopy(sconf[sconf[builder]['inherit']])
        if 'inherit' in computed_config:
            computed_config.update(deepcopy(sconf[computed_config['inherit']]))
        computed_config.update(sconf[builder])
    else:
        computed_config = deepcopy(sconf[builder])

    if 'editions' in sconf:
        computed_config.builder = builder.split('-')[0]
        if 'edition' not in computed_config:
            raise Exception('[sphinx] [error]: builds with editions must specify an edition.')
    else:
        computed_config.edition = None

    if 'builder' not in computed_config:
        computed_config.builder = builder

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

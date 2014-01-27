from multiprocessing import cpu_count
import pkg_resources

def is_parallel_sphinx(version):
    if version in [ '1.2b1-xgen', '1.2b2', '1.2b3', '1.2', '1.2.1']:
        return True
    elif [ int(n) for n in version.split('.') ][1] >= 2:
        return True

    return False

def get_sphinx_args(sconf, conf):
    o = []

    o.append(get_tags(sconf.builder, sconf))
    o.append('-q')
    o.append('-b {0}'.format(sconf.builder))

    if (is_parallel_sphinx(pkg_resources.get_distribution("sphinx").version) and
        conf.project.name != 'mms'):
        o.append(' '.join( [ '-j', str(cpu_count() + 1) ]))

    o.append(' '.join( [ '-c', conf.paths.projectroot ] ))

    if 'language' in sconf:
        o.append("-D language='{0}'".format(sconf.language))

    return ' '.join(o)

def compute_sphinx_config(builder, sconf, conf):
    if 'inherit' in sconf[builder]:
        computed_config = sconf[sconf[builder]['inherit']]
        computed_config.update(sconf[builder])
    else:
        computed_config = sconf[builder]

    if conf.project.name == 'mms':
        computed_config.builder = builder.split('-')[0]
        if 'edition' not in computed_config:
            raise Exception('[sphinx] [error]: mms builds must have an edition.')
    else:
        computed_config.builder = builder
        computed_config.edition = None

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

from copy import deepcopy

## this renders the legacy config

def render_sphinx_config(conf):
    computed = {}

    def resolver(v, conf, computed):
        while 'inherit' in v:
            if v['inherit'] in computed:
                base = deepcopy(computed[v['inherit']])
            else:
                base = deepcopy(conf[v['inherit']])

            del v['inherit']
            base.update(v)
            v = base

        return v

    to_compute = []

    for k,v in conf.items():
        v = resolver(v, conf, computed)
        computed[k] = v

        if 'languages' in v:
            to_compute.append((k,v))

    for k, v in to_compute:
        if k in ['prerequisites', 'generated-source',
                 'sphinx-builders'] or 'base' in k:
            continue

        if 'languages' in v:
            for lang in v['languages']:
                computed['-'.join([k,lang])] = resolver({ 'inherit': k,
                                                          'language': lang },
                                                        conf, computed)

    for i in computed.keys():
        if i in ['prerequisites', 'generated-source',
                 'sphinx-builders'] or 'base' in i:
            del computed[i]

    return computed

import os.path
import logging

import sphinx

from giza.strings import hyph_concat
from giza.config.base import RecursiveConfigurationBase
from giza.serialization import ingest_yaml_doc

logger = logging.getLogger('giza.config.sphinx')

#################### Ingestion and Rendering ####################

def is_legacy_sconf(conf):
    if 'v' not in conf or conf['v'] == 0:
        return True
    else:
        return False

def get_sconf_base(conf):
    sconf_path = os.path.join(conf.paths.projectroot, conf.paths.builddata, 'sphinx.yaml')

    return ingest_yaml_doc(sconf_path)

def render_sconf(edition, builder, language, conf):
    sconf_base = get_sconf_base(conf)

    if is_legacy_sconf(sconf_base):
        # this operation is really expensive relative to what we need and how often
        # we have to do it:
        return resolve_legacy_sphinx_config(sconf_base, edition, builder, language)
    else:
        raise NotImplementedError
        sconf = SphinxConfig()
        sconf.ingest(sconf_base)
        sconf.register(builder, langauge, edition)

        return sconf

#################### New-Style Config Object ####################

class SphinxConfig(RecursiveConfigurationBase):
    _option_registry = [ 'edition', 'language' ]

    def __init__(self, conf, input_obj=None):
        # register the global config, but use our ingestion
        super(SphinxConfig, self).__init__(None, conf)
        self._raw = {}
        self.ingest(input_obj)

    def ingest(self, input_obj=None):
        if input_obj is None:
            input_obj = get_sconf_base()

        if is_legacy_sconf(input_obj):
            self._raw = render_sphinx_config(input_obj)
        else:
            self._raw = input_obj

    def register(self, builder, language, edition):
        self.language = language
        self.builder = builder
        self.edition = edition

        if edition is None:
            lookup = self.builer
        else:
            lookup = hyph_concat(self.builder, self.edition)

        base = self._raw[lookup]

        for i in ['excluded_files', 'tags', 'languages']:
            if i in base:
                setattr(self, i, base[i])

        m = 'registered language, builder, and edition options: ({0}, {1}, {2})'
        logger.debug(m.format(language, builder, edition))

    @property
    def builder(self):
        if 'builder' not in self.state['builder']:
            return 'html'
        else:
            return self.state['builder']

    @property
    def excluded_files(self):
        return self.state['excluded_files']

    @property
    def tags(self):
        return self.state['tags']

    @property
    def langauges(self):
        return self.state['langauges']

    @builder.setter
    def builder(self, value):
        if value not in sphinx.builders.BUILTIN_BUIDLERS:
            raise Exception('{0} is not a valid sphinx builder'.format(value))
        else:
            self.state['builder'] = value

    @excluded_files.setter
    def excluded_files(self, value):
        if not isinstance(value, list):
            logger.error('excluded_files must be a list.')
            raise TypeError
        else:
            self.state['excluded_files'] = value

    @tags.setter
    def tags(self, value):
        if not isinstance(value, list):
            logger.error('builder tags must be a list.')
            raise TypeError
        else:
            self.state['tags'] = value

    @langauges.setter
    def langauges(self, value):
        if not isinstance(value, list):
            logger.error('langauges must be a list.')
            raise TypeError
        else:
            self.state['langauges'] = value


#################### Rendering for Legacy Config ####################

from copy import deepcopy

def resolve_legacy_sphinx_config(sconf_base, edition, builder, language):
    sconf_base = render_sphinx_config(sconf_base)

    if edition is not None:
        builder = '-'.join([builder, edition])

    sconf = sconf_base[builder]

    sconf['edition'] = edition
    if 'builder' not in sconf:
        sconf['builder'] = builder

    if language is not None:
        sconf['language'] = language

    return sconf

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
